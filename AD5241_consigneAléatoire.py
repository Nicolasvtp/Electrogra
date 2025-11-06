#but : vérifier la tension du potentiomètre numerique avec l'ADS1115 : tension theorique != tension mesuree
import time
import ADS1x15
from smbus2 import SMBus
from gpiozero import LED
from random import randint

adresseADS1115 = 0x48
channelADS1115 = 1 #bus
ADS = ADS1x15.ADS1115(channelADS1115, adresseADS1115) #création de l'objet ADS1115
ADS.setGain(ADS.PGA_6_144V) #définition de la gamme de tension (de -6.144 V à + 6.144 V)
ADS.readADC(0) #envoyer un byte de ces infos

adresseAD5241 = 0x2C

registreInterne = 0x00
bus = SMBus(1)

Potentiometre = LED(26)
Potentiometre.off()
Potentiometre.on()

while True : 
    #changer la position du potentiometre numerique aléatoirement --> OK
    positionMin = 0
    positionMax = 255 #8 bits disponibles = 256  positions
    positionCible = randint(positionMin, positionMax) #choix aléatoire de la position entre 0 et 255
    print(f"PositionCible : {positionCible}/255")

        #communication Raspberry <=> potentiometre par bus i2c
    bus.write_i2c_block_data(adresseAD5241, registreInterne, [positionCible])
    time.sleep(1)

    lectureEA = ADS.readADC(2) #lecture de la valeur de tension de l'electrode auxiliaire (adresse 2 de l'ADS1115) en signal analogique
    tensionEA = ADS.toVoltage(lectureEA) #conversion en signal numérique
    tensionEA = tensionEA * 11 #conversion propre à l'ADS1115
    print(f"lectureEA : {lectureEA} // tensionEA = {tensionEA:.3f} V")

    lectureET = ADS.readADC(0) #adresse 0 de l'ADS1115 = electrode de travail
    tensionET = ADS.toVoltage(lectureET)
    tensionET = tensionET * 11
    print(f"lectureET : {lectureET} // tensionET = {tensionET:.3f} V")

    deltaLecture = lectureEA - lectureET
    deltaTension = tensionEA - tensionET
    print(f"deltaLecture = {deltaLecture} // deltaTension = {deltaTension:.3f} V")

        #communication AD5241 <=> Raspberry
    lectureAD5241 = bus.read_byte_data(adresseAD5241, registreInterne)
    print(f"lecture AD5241 : {lectureAD5241}/255")
        #calcul de la tension theorique, a comparer avec mesure en reel entre EA et ET
    tensionPotTh = 11 * lectureAD5241 * 2*6.144 / 2**16
    # 11 : conversion propre a ADS1115
    # 6.144 V multiplié par 2 pour avoir domaine de tension allant de -6.144 V à +6.144 V (PGA modifiable avec setGain, voir fichier ADS1x15.py pour les differentes valeurs possibles)
    # 2**16 : les 16 bits de l'ADS1115 (modifiable dans ADS1x15.py : _adcBits)
    print(f"tension théorique aux bornes du pot num : {tensionPotTh:.3f} V")

    #Conversion du signal analogique en signal numérique (valeur de tension en V), 
    tensionADS = ADS.toVoltage(deltaLecture)*11
    #tension = 0.375 - tensionADS
    print(f"Tension = {tensionADS:.3f} V")
    print("")
    time.sleep(2)
