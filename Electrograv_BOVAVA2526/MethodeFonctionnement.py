import time
import sqlite3
import datetime
import smbus
from gpiozero import LED, PWMLED
import ADS1x15

class ConstantVoltageController:
    def __init__(self):
        # Initialisation des paramètres
        self.bus = smbus.SMBus(1)
        self.ads = ADS1x15.ADS1115(1, 0x48)
        self.ads.setGain(self.ads.PGA_6_144V)
        self.ads.setDataRate(self.ads.DR_ADS111X_860)
        self.ads.setMode(self.ads.MODE_SINGLE)
        
        # Configuration des GPIO
        self.potentiometer = LED(26)

        # État initial
        self.potentiometer.off()

        # Variables de contrôle
        self.voltage_setpoint = 0
        self.test_duration = 0

    def write_potentiometer(self, value):
        """Écrit la valeur dans le potentiomètre via I2C."""
        # Adresse I2C du potentiomètre
        potentiometer_address = 0x2C  # Remplacez par l'adresse correcte de votre potentiomètre

        # Écriture de la valeur dans le registre du potentiomètre
        self.bus.write_i2c_block_data(potentiometer_address, 0x00, [value])

    def apply_constant_voltage(self, voltage, test_duration):
        """Applique une tension constante entre l'anode et la cathode."""
        self.voltage_setpoint = voltage
        start_time = datetime.datetime.now()
        print(f"Applying constant voltage: {self.voltage_setpoint} V")

        while True:
            # Lire la tension actuelle
            current_voltage = self.read_voltage()
            print(f"Current voltage: {current_voltage} V")

            # Vérifier si la tension est dans la marge d'erreur
            error_margin = 0.02 #erreur de 2%
            if abs(current_voltage - self.voltage_setpoint) > error_margin:
                self.regulate_voltage(current_voltage)
            else:
                print("Voltage is stable.")

            # Vérifier la durée du test
            if (datetime.datetime.now() - start_time).total_seconds() >= test_duration:
                print("Test duration reached. Stopping.")
                break

            time.sleep(0.1)  # Attendre un court instant avant la prochaine lecture

    def read_voltage(self):
        """Lit la tension à l'aide de l'ADS1115."""
        raw_value = self.ads.readADC(0)  # Lecture de l'ADC
        voltage = self.ads.toVoltage(raw_value) * 11  # Conversion en tension
        return voltage

    def regulate_voltage(self, current_voltage):
        """Régule la tension appliquée en ajustant la résistance."""
        calculated_resistance = (self.voltage_setpoint / 0.00001)  # Exemple de calcul
        applied_resistance = min(max(calculated_resistance, 0), 255)  # Limiter la résistance

        # Écriture de la résistance dans le potentiomètre
        self.write_potentiometer(applied_resistance)
        print(f"Adjusted resistance to: {applied_resistance}")

# Exemple d'utilisation
if __name__ == "__main__":
    controller = ConstantVoltageController()
    controller.apply_constant_voltage(5,60)  # Appliquer 5V pendant 60secondes