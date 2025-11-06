#but : vérifier la tension du potentiomètre numerique avec l'ADS1115
#ATTENTION : position du potentiometre physique importe la tension de sortie, pourquoi??
#les tests renseignés en commentaires ont été réalisés sur potentiometre physique réglé sur la position en tournant au max dans sens horlogique
import time
import ADS1x15
from smbus import SMBus
from gpiozero import LED

#initialisation
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

#changer la position du potentiometre numerique pour se rapprocher de la tension de consigne
ValeurMaxPot = 1000000 #ohm
DivisionsPot = 256 #8bits
duree = 600 #600secondes = 10minutes
tensionConsigne = 4 #V
print(f"Consigne : {tensionConsigne} V")
erreurMax = 0.1 #V, erreur max entre tension mesuree et tension de consigne

#calculer la resistance (du potentiometre numerique) correspondant a la tension de consigne via le LT3080
ValeurResistanceCalculee=(float(tensionConsigne))/0.00001 #R=U/I, le courant de 10µA circulant dans le LT3080
print("valeurResistanceCalculee: " + str(ValeurResistanceCalculee) +" ohm")
ValeurResistanceCalculee= round(ValeurResistanceCalculee)
print("ValeurResistanceCalculee arrondie: " + str(ValeurResistanceCalculee) + " ohm")
#determiner la position correspondant du potentiometre numerique
position = (ValeurResistanceCalculee/ValeurMaxPot)*DivisionsPot
position = round(position)
print("position: " + str(position))

for i in range(duree): #boucle pendant 10minutes
    bus.write_i2c_block_data(adresseAD5241, registreInterne, [position])
    
    lectureAD5241 = bus.read_byte_data(adresseAD5241, registreInterne)
    print(f"lecture AD5241 : {lectureAD5241}/255")
    lectureEA = ADS.readADC(2) #lecture de la valeur de tension en signal analogique
    tensionEA = ADS.toVoltage(lectureEA)
    tensionEA = tensionEA * 11 #conversion ADS1115
    print(f"tension actuelle = {tensionEA:.3f} V")
    
    comparaisonTensions = abs(tensionConsigne - tensionEA)

    #regulation
        #tension mesuree initialement pour EA = 7.456 V et ET = 0 V
    if (comparaisonTensions >= erreurMax):
        if (tensionEA > tensionConsigne): 
            position -= 1
            print(f"position : {position}/255")
            if position <= 0:
                position = 0 #position minimale. Sans cette limite : la position retourne a 255 
                print(f"position : {position}")
                #Soucis : uniquement positions 0;1;2;3 modifient la tension
                #tension minimale : en position 0 ~= 3.250 V et position 3 ~= 7.456 V
        else :
            position += 1
            print(f"position : {position}")
            if position >= 255:
                position = 255 #position maximale. Sans cette limite : position retourne a 0 
                print(f"position : {position}")
                #Soucis : la tension ne change jamais, reste à 7.456 V
    bus.write_i2c_block_data(adresseAD5241, registreInterne, [position])
    time.sleep(0.1)
Potentiometre.off()