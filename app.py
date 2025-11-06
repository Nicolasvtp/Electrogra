
import time
import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk
from gpiozero import LED, PWMLED

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from matplotlib import style
from random import randint

import smbus
import ds1307 as rtc
import ADS1x15


LongeurEntreesSorties =13  # pour la définition de la taille des objets sur la fenetre graphique
LongeurConsignes =8  # pour la définition de la taille des objets sur la fenetre graphique
decallagex =2
decallagey =5

# Get I2C bus
bus = smbus.SMBus(1)

ad5241Addr =0x2C                       #addresse I2C du potentiomètre
ValeurMaxPot =1000000
DivisionsPot =256

derniereValeurResistanceAppliquee =0

TypeDeGraphique = 1    #1 Courant  = f(tenmps) 
                       #2 tension différentielle = f(courant)

TensionRegulee5V =5
PourcentErrSurConsignes =2           # % pourcentage d'erreur sur la consigne
PourcentAlerte = 80                    #deniit à quel pourcentage de la durée du test on declenche un alerte
pulsee = 0                             #definit si on a déjà alerté ou pas 

tempsEnregistrementBD =2              # valeur definie en secondes 

tempsattente = 0.01     #definit  le temps d'attente avant lecture dans les boucles de regulation

mode_de_test =0 # 0 tension constante
                # 1 courant constant
                # 2 tension conctrolée
                # 3 courant controlé

numero_courant_enregistrement =1     # definit le numéro de l'enregistrement pour le test en cours 
numero_enregistrement_a_afficher =1  # definit le numéro de l'enregistrement selectionné, à afficher 
nombreTestsBD =0             # definit le nombre de test(s) effectué() dont données sont présente dan la BD  

mode_pc_pc =0            #variable du mode potentiel contant ou bien potentiel controlé
mode_tc_cc =0            #variable du mode commande à tension constante ou bien courant constant. tension constante ou bien courant constant
mode_de_branchement =0   #variable du mode de branchement des electrodes dans la solution. banchement normal(CE, ER, ET) ou inverse sur les éléctrodes entrées/sorties
                         #permet de connaitre le type  d'analyse

mode_marche_arret =0     # variable du mode marche ou bien arrêt 

mode_pc_t_c =0           # variable du mode potentiel controlé en tension ou bien en courant 

TensionConsigne =0       # variable de tension à incrementer ou pas selon le mode mode potentiel controlé ou constant 
CourantConsigne =0       # variable de courant à incrementer ou pas selon le mode mode potentiel controlé ou constant
CptrDelaisIncrConsigne =0    # variable de l'interval à incrementer pour le mode potentiel controlé

TensionConsigneEnregistree =0     # variables de consignes enreguistées lors de la mise en fonctionnement 
CourantConsigneEnregistree  =0    #
DureeDuTestEnregistree =0         #
DelaisIncrConsigneEnregistree =0  #

ErreurCouranteTension =0
ErreurCouranteCourant =0

ErreurCourante =0.0
ErreurEnregistree =0.0

valeurCouranteTension =0.0   # variable de mesure tension      
valeurCouranteCourant =0.0   # variable de mesure courant

tensionET =0.0
tensionEREF =0.0 

Date          =""
DateDebutTest =""
DateFinTest   =""

LocalDateDebutTest = datetime.datetime.now()
LocalDateEnCours   = datetime.datetime.now()

LocalDateIncrConsigne     = datetime.datetime.now()
LocalDateEnregistrementBD = datetime.datetime.now()
 
try:
#     print ("connexion à la BD")
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()                
    req = cursor.execute('SELECT numero_test FROM mesures')
    nombre  = req.fetchall()
    nombreTestsBD = nombre[-1][0]
#     print("nombreTestsBD : ", str(nombreTestsBD))
    numero_courant_enregistrement = nombreTestsBD + 1
#     print("numero_courant_enregistrement : ", str(numero_courant_enregistrement))
    
except Exception as e:
    connection.rollback() #faire un retour en arrière par rapporrt à une requette qui s'est mal passée
    print("[ERREUR SUR LA BD] :", e)

finally:
    connection.close()

#initialisation de l'ADS1115
ADS1115 = ADS1x15.ADS1115(1, 0x48)           # ADS1115 physiquement défini à l'adresse 0x48, avec sa broche ADDR reliée à la masse
ADS1115.setGain(ADS1115.PGA_6_144V)          # On prend le gain le plus bas (index 0), pour avoir la plus grande plage de mesure (6.144 volt)
ADS1115.setDataRate(ADS1115.DR_ADS111X_860)  # On spécifie la vitesse de mesure de tension qu'on souhaite, allant de 0 à 7 (7 étant le plus rapide, soit 860 échantillons par seconde)
ADS1115.setMode(ADS1115.MODE_SINGLE)         # On indique à l'ADC qu'on fera des mesures à la demande, et non en continu (0 = CONTINUOUS, 1 = SINGLE)
ADS1115.readADC(0)                           # Et on fait une lecture à vide, pour envoyer tous ces paramètres

Potentiometre = LED(26)
Buzzer = LED(5)
Sens01 = LED(17)
Sens02 = LED(27)
Pwm0 = PWMLED(18)

Buzzer.off()
Potentiometre.off()
Sens01.on()
Sens02.off()
Pwm0.value=0

frames_boutons = []

def MessageTestEnCours() :
    global mode_marche_arret
    if mode_marche_arret > 0:
        print("Aucune action possible lorsqu'un test en cours ...")
    return mode_marche_arret

def pulse(freq = 1, temp = 1) :  # will take freq and temp in the future
    for i in range(15):
        Buzzer.on()
        time.sleep(0.05)
        Buzzer.off()
        time.sleep(0.05)

def Ecriture_ad5241(reg, values=[]):
    bus.write_i2c_block_data(ad5241Addr, reg, values)

def Lecture_ad5241(reg):
    value = bus.read_byte_data(ad5241Addr, reg)
    return value

def regulationTension (tension:int, erreur:float):
    print()
    print("regulationTension()")
    global valeurCouranteTension
    global ErreurCouranteTension
    global tempsattente
    global derniereValeurResistanceAppliquee
    
#     print("tension à reguler: " + str(tension) +" mV")
#     print("erreur : " + str(erreur) +" mV")

    ValeurResistanceCalculee=(float(tension)*0.001)/0.00001
#     print("valeurResistanceCalculee: " + str(ValeurResistanceCalculee) +" ohm")
    ValeurResistanceCalculee= round(ValeurResistanceCalculee)
#     print("ValeurResistanceCalculee arondie: " + str(ValeurResistanceCalculee))
    
    ValeurResistanceAAppliquer= (DivisionsPot*ValeurResistanceCalculee)/ValeurMaxPot
#     print("ValeurResistanceAAppliquer: " + str(ValeurResistanceAAppliquer))

    ValeurResistanceAAppliquer= round(ValeurResistanceAAppliquer)
#    print("ValeurResistanceAAppliquer: " + str(ValeurResistanceAAppliquer))

    if(derniereValeurResistanceAppliquee > 0):
        ValeurResistanceAAppliquer = derniereValeurResistanceAppliquee
        
    if (ValeurResistanceAAppliquer > 255) :
        ValeurResistanceAAppliquer=255
    
    liste = [ValeurResistanceAAppliquer]
#     print(liste)
    Ecriture_ad5241(0x00, liste)
    Tensionlue =0
    comprare =0
    ErreurEntree = erreur
    compteur =0
    time.sleep(tempsattente)
    time.sleep(tempsattente)
    time.sleep(tempsattente)
    time.sleep(tempsattente)
    
    while True:
        Tensionlue = ADS1115.readADC(2)
#         print("Tensionlue: " + str(Tensionlue))
        Tensionlue = ADS1115.toVoltage(Tensionlue)*11   # la tension réelement lue est divisée par 11
#         print("Tensionlue: " + str(Tensionlue))
        Tensionlue = Tensionlue * 1000            #conversion en mV
#         print("Tensionlue: " + str(Tensionlue))
        comprare = Tensionlue - tension
#         print("comprare: " + str(comprare))
        
        if (comprare < 0 and abs(comprare) > ErreurEntree) :    # comparaison avec une esseur à 20 mV
#             print("=> Augmenter la tension")
#             print("Tensionlue - tension < -", str(ErreurEntree))
            ValeurResistanceAAppliquer  += 1
            liste = [ValeurResistanceAAppliquer]
#             print(liste)
            Ecriture_ad5241(0x00, liste)
            
        elif (comprare > ErreurEntree):
#             print("=> Diminuer la tension")
#             print("Tensionlue - tension > ", str(ErreurEntree))
#             print(liste)
            ValeurResistanceAAppliquer  = ValeurResistanceAAppliquer-1
            liste = [ValeurResistanceAAppliquer]
            Ecriture_ad5241(0x00, liste)
       
        else:
            print("erreur sur Tensionlue - tension e[-", str(ErreurEntree), "," ,str(ErreurEntree),"] mV", )
            break
        
        break
        time.sleep(tempsattente)
        compteur +=1
        if (compteur > 10 ) :
           compteur =0
           ErreurEntree += erreur/2
#            print("nouvelle valeur de d'erreur", str(ErreurEntree))
#         
#         print("compteur = ", str(compteur))
           
#     print(liste)
    derniereValeurResistanceAppliquee = ValeurResistanceAAppliquer
    valeurCouranteTension = Tensionlue
    ErreurCouranteTension = comprare
    return valeurCouranteTension , ErreurCouranteTension

def regulationCourant (courant:int, erreur:float):
    print()
    print("regulationCourant()")
    global valeurCouranteCourant
    global ErreurCouranteCourant
    global tempsattente
    global derniereValeurResistanceAppliquee
    
#     print("courant à reguler: " + str(courant) +" mA")
#     print("erreur : " + str(erreur) +" mA")
    
    ValeurTensionAAppliquer = float(courant)*0.001*0.5 #0.5 ohm est la resistance initiale de la solution
#     print("ValeurTensionAAppliquer: " + str(ValeurTensionAAppliquer) +" V")

    ValeurTensionAAppliquer = 5
#     print("ValeurTensionAAppliquer: " + str(ValeurTensionAAppliquer) +" *V")
    ValeurResistanceCalculee=((ValeurTensionAAppliquer))/0.00001                    # Vout = Rset*10µA
#     print("valeurResistanceCalculee: " + str(ValeurResistanceCalculee) +" ohm")
#     ValeurResistanceCalculee= round(ValeurResistanceCalculee)
#     print("ValeurResistanceCalculee arondie: " + str(ValeurResistanceCalculee))
    
    ValeurResistanceAAppliquer= (DivisionsPot*ValeurResistanceCalculee)/ValeurMaxPot
#     print("ValeurResistanceAAppliquer: " + str(ValeurResistanceAAppliquer))

    ValeurResistanceAAppliquer = round(ValeurResistanceAAppliquer)
#     print("ValeurResistanceAAppliquer: " + str(ValeurResistanceAAppliquer))

    if (derniereValeurResistanceAppliquee > 0) :
        ValeurResistanceAAppliquer = derniereValeurResistanceAppliquee

    if (ValeurResistanceAAppliquer > 255) :
        ValeurResistanceAAppliquer=255
        
    liste = [ValeurResistanceAAppliquer]
#     print(liste)
    Ecriture_ad5241(0x00, liste)
#    Potentiometre.on() #mettre à on dans le demarrage du test Potentiometre
    Courantlue =0
    comprare =0
    ErreurEntree = erreur
    compteur = 0
    time.sleep(tempsattente)
    time.sleep(tempsattente)
    time.sleep(tempsattente)
    time.sleep(tempsattente)
    while True:
        Tensionlue = ADS1115.readADC(3)
#         print("Tensionlue: " + str(Tensionlue))
        Courantlue = ADS1115.toVoltage(Tensionlue)/5  #Vout = (Rshunt=25mohm)*Iload*200 + (vref=0)
#         print("Courantlue: " + str(Courantlue))
        Courantlue = Courantlue * 1000                # conversion en mA
#         print("Courantlue: " + str(Courantlue))
        comprare = Courantlue - courant
#         print("comprare: " + str(comprare))
        if (comprare < 0 and abs(comprare) > abs(ErreurEntree)) :
#             print("=> Augmenter le courant")
#             print("Courantlue - courant < -", str(ErreurEntree), " mA")
            ValeurResistanceAAppliquer  +=1
            liste = [ValeurResistanceAAppliquer]
#             print(liste)
            Ecriture_ad5241(0x00, liste)
        elif (comprare > ErreurEntree):
#             print("=> Diminuer le courant")
#             print("Courantlue - courant > ", str(ErreurEntree), " mA")
#             print(liste)
            ValeurResistanceAAppliquer  -=1
            liste = [ValeurResistanceAAppliquer]
            Ecriture_ad5241(0x00, liste)
        elif (ValeurResistanceAAppliquer > 255) :
            ValeurResistanceAAppliquer = 255
            break
        else:
#             print("erreur sur Courantlue - courant e[-",str(ErreurEntree), ",", str(ErreurEntree), "] mA")
            break
        time.sleep(tempsattente)
        compteur +=1

        if (compteur > 5) :
           compteur =0
           ErreurEntree += erreur/2
#            print("nouvelle valeur de d'erreur", str(ErreurEntree))
#         print("compteur = ", str(compteur))
#     print(liste)
    derniereValeurResistanceAppliquee = ValeurResistanceAAppliquer 
    valeurCouranteCourant = Courantlue
    ErreurCouranteCourant = comprare
    return valeurCouranteCourant, ErreurCouranteCourant

def lectureHorloge() :
    seconds = rtc.ds1307_get_seconds()
    minutes = rtc.ds1307_get_minutes()
    hours = rtc.ds1307_get_hours()
#    day = rtc.ds1307_get_day()
    date = rtc.ds1307_get_date()
    month = rtc.ds1307_get_month()
    year = rtc.ds1307_get_year()
    DateTime = str("{0:02}".format(date)) + "/" + str("{0:02}".format(month)) + "/" + str("{0:04}".format(year)) + " " + str("{0:02}".format(hours)) + ":" + str("{0:02}".format(minutes)) + ":" + str("{0:02}".format(seconds))   
    return DateTime 

def LectureEntreeEtMiseAJour() :
    global mode_marche_arret
    global TensionRegulee5V
    global ErreurEnregistree
    global valeurCouranteTension
    global valeurCouranteCourant
    global tensionET
    global tensionEREF
    global TensionConsigne
    global CourantConsigne

    #lecture des tensions
    lecture = ADS1115.readADC(0)          # lecture de la valeur numérique de la tension à l'électrode de travail 
    tension = ADS1115.toVoltage(lecture)  #  conversion en tension : fonction des paramètres initiaux du converstisseur
    tensionET = tension*11*1000           # tension reelle à l'electrode de travail
    sortieET.delete(0, tk.END)            # la tension reelle divisée par 11 (pont diviseur de resistances 10k et 1k)  et conversion en mV
    sortieET.insert(0, round(tensionET))           
                                    
    lecture = ADS1115.readADC(1)                        # lecture de la valeur numérique de la tension à l'electrode de reference 
    tension = ADS1115.toVoltage(lecture)
    tensionEREF = (tension*12 - TensionRegulee5V)*1000 # la tension reelle est ajoutée de la TensionRegulee5V
    sortieEREF.delete(0, tk.END)                       # et le tout divisé par 12. pont en T adapté 10k à VCC 1K à la massse 10K à Vin (pont diviseur de resistances 10k et 1k)
    sortieEREF.insert(0, round(tensionEREF))           # et conversion en mV                                

    lecture = ADS1115.readADC(2)          # lecture de la valeur numérique de la tension regulée pour la solution  
    tension = ADS1115.toVoltage(lecture)
    valeurCouranteTension = tension*11*1000
    sortieCE.delete(0, tk.END)
    sortieCE.insert(0, round(valeurCouranteTension))
    sortieTension.delete(0, tk.END)
    sortieTension.insert(0, round(valeurCouranteTension))

    lecture = ADS1115.readADC(3)            # lecture de la tension correspondante à le mesure du courant  
    tension = ADS1115.toVoltage(lecture)
    valeurCouranteCourant = (tension/5)*1000              # Vout = Iload * Rshunt * 200 + (Vref=0) Rshunt = 25mohm 
    sortieCourant.delete(0, tk.END)
    sortieCourant.insert(0, round(valeurCouranteCourant))   # => la value de tension lue doit être divisée par 5 pour avoir le courant
    sortieCourantTest.delete(0, tk.END)
    sortieCourantTest.insert(0, round(valeurCouranteCourant))

    sortieErrTension.delete(0, tk.END)
    sortieErrCourant.delete(0, tk.END)
    
    if (mode_de_test == 1 or mode_de_test == 3 ) :
        sortieErrTension.insert(0, round(valeurCouranteCourant - CourantConsigne))
        sortieErrCourant.insert(0, round(valeurCouranteCourant - CourantConsigne))
    
    elif (mode_de_test == 0 or mode_de_test == 2 ) :
        sortieErrTension.insert(0, round(valeurCouranteTension - TensionConsigne))
        sortieErrCourant.insert(0, round(valeurCouranteTension - TensionConsigne)) 

def get_back_values():
    "Dummy function"
    x = range(10)
    y1 = [randint(0, 10) for i in range(10)]
    return x, y1

#     x, y1 = get_back_values()
#     ax1.clear()
#     ax1.set_ylim(0, 10, auto=True)
#     ax1.set_ylabel('tension differentielle (mV)', color='g')
#     ax1.set_xlabel('courant (mA)', color='r')
#     ax1.plot(x, y1, 'g-o')

def update_graph(dt):
    global mode_marche_arret
    global mode_de_test
    global CourantConsigneEnregistree
    global TensionConsigneEnregistree
    global TensionConsigne
    global CourantConsigne
    global CptrDelaisIncrConsigne
    global valeurCouranteTension
    global valeurCouranteCourant
    global pulsee
    global DelaisIncrConsigneEnregistree
    global Date
    global ErreurCourante
    global ErreurEnregistree
    global tempsEnregistrementBD   # valeur definie en secondes 
    global mode_de_branchement
    global LocalDateDebutTest
    global LocalDateEnCours
    global LocalDateIncrConsigne      
    global LocalDateEnregistrementBD 
    global PourcentAlerte
    global tensionET
    global tensionEREF
    global TypeDeGraphique
    global derniereValeurResistanceAppliquee
    
    LocalDateEnCours = datetime.datetime.now()
    Date = lectureHorloge()
    sortieDate.delete(0, tk.END)
    sortieDate.insert(0, Date)
    
    if(mode_marche_arret > 0) :  # test si système en marche
        #print("test en cours ..."   
        if (LocalDateEnCours.timestamp() - LocalDateDebutTest.timestamp() >= (PourcentAlerte/100)*DureeDuTestEnregistree) :  #biper le buzzer si on a ateint PourcentAlerte % du temps du test
            if (pulsee == 0) :
                pulse()
                pulsee =1       
            
        if((LocalDateEnCours.timestamp() - LocalDateDebutTest.timestamp() >= DureeDuTestEnregistree)) : # fin de la durée du test atteint ? si oui arreter le test                       
#             print("arret test")   # DureeDuTestEnregistree convertie en secondes
            ActionButtonA()       #arrêter le test  #mettre à jour les infos
            return 
            
        if(mode_de_test == 3 ) :  # test si mode potentiel controlé en Courant
#             print("*mode potentiel controlé en Courant*")
#             print("CptrDelaisIncrConsigne : ", str(CptrDelaisIncrConsigne), " s")

            if ((datetime.datetime.now().timestamp() - LocalDateIncrConsigne.timestamp()) > DelaisIncrConsigneEnregistree ) :
#                 print("delais sur la consigne de courant atteinte")
                CptrDelaisIncrConsigne = 0 
                CourantConsigne += CourantConsigneEnregistree
                MaxCourantConsigne = int((listeCourant[-1])[:-3])
                if (CourantConsigne > MaxCourantConsigne ) :
                    CourantConsigne = MaxCourantConsigne
                
                lachaine = str(CourantConsigne) + " mA"
                laliste = listeCombCourant['values']
                for i in range(len(laliste)) :
                    if (laliste[i] == lachaine):
                        listeCombCourant.current(i)
                        break       
                ErreurCourante = (CourantConsigne*PourcentErrSurConsignes)/100
                derniereValeurResistanceAppliquee =0
                valeurCouranteCourant, ErreurEnregistree = regulationCourant(CourantConsigne, ErreurCourante)  # peut recuperer directement la valeur du courant regulé et l'erreur lié
                LocalDateIncrConsigne = datetime.datetime.now() 
            elif(abs(valeurCouranteCourant - CourantConsigne) > abs(ErreurEnregistree)) :
#                 print("l'erreur sur la consigne en courant a changée !")
                ErreurCourante = (CourantConsigne*PourcentErrSurConsignes)/100
                valeurCouranteCourant, ErreurEnregistree = regulationCourant(CourantConsigne, ErreurCourante)
#                 print("mise à jour de la regulation de Courant : ", str(CourantConsigne), " mA en mode :", str(mode_de_test))
             
#             print("CourantConsigne : ", str(CourantConsigne), " mA")
            
        elif (mode_de_test == 2) : # mode potentiel controlé en Tension
#             print("*mode potentiel controlé en Tension*")
            if ((datetime.datetime.now().timestamp() - LocalDateIncrConsigne.timestamp()) > DelaisIncrConsigneEnregistree ) :
#                 print("delais sur la consigne de tension atteinte")
                CptrDelaisIncrConsigne = 0 
                TensionConsigne += TensionConsigneEnregistree
                MaxTensionConsigne = int((listeTension[-1])[:-3])
                if (TensionConsigne > MaxTensionConsigne) :
                    TensionConsigne = MaxTensionConsigne  # recupération du dernier élement de la liste deroulante des tensions
    
                lachaine = str(TensionConsigne) + " mV"
                laliste = listeCombTension['values']
                for i in range(len(laliste)) :
                    if ((laliste[i]) == lachaine) :
                        listeCombTension.current(i)
                        break
                
                derniereValeurResistanceAppliquee =0
                ErreurCourante= (TensionConsigne*PourcentErrSurConsignes)/100
                valeurCouranteTension, ErreurEnregistree = regulationTension(TensionConsigne, ErreurCourante)
                LocalDateIncrConsigne = datetime.datetime.now() 
            
            elif (abs(valeurCouranteTension - TensionConsigne) > abs(ErreurEnregistree)) :
#                 print("l'erreur sur la consigne en de tension a changée !")
                ErreurCourante = (TensionConsigne*PourcentErrSurConsignes)/100                
                valeurCouranteTension, ErreurCourante = regulationTension(TensionConsigne, ErreurCourante)
#                 print("mise à jour de la regulation de tension à :", str(TensionConsigne), "mV en mode :", str(mode_de_test))
            
#             print("TensionConsigne : ", str(TensionConsigne), " mV") 
                
        elif(mode_de_test == 1) :  #mode potentiel constant en Courant
#             print() 
#             print("* mode potentiel constant en Courant*")
#             print("valeurCouranteCourant ", str(valeurCouranteCourant), "mA", "CourantConsigneEnregistree", str(CourantConsigneEnregistree),"mA")
            if(abs(valeurCouranteCourant - CourantConsigneEnregistree) > abs(ErreurEnregistree) ) :
                ErreurCourante = ((CourantConsigne*PourcentErrSurConsignes)/100)
                valeurCouranteCourant, ErreurEnregistree = regulationCourant(CourantConsigne, ErreurCourante)
#                 print()
#                 print("mise à jour de la regulation de Courant à :", str(CourantConsigne), " mA en mode :", str(mode_de_test))
#                 print("erreur enregistrée : ", str(ErreurEnregistree), " mA sur consigne :", str(valeurCouranteCourant), " mA")
                
        elif (mode_de_test == 0) :  #mode potentiel constant en Tension
            print()
#             print("*mode potentiel constant en Tension*")
#             print("* valeur Courante tension de Consigne", str(TensionConsigne))
#             print("* valeur tension de Consigne save", str(TensionConsigneEnregistree))
#             print("* valeur Courante tension", str(valeurCouranteTension))
#             print("* valeur Courante erreur ", str(ErreurEnregistree), "comparée à : ", str((valeurCouranteTension-TensionConsigne)))
            ErreurCourante = ((TensionConsigne*PourcentErrSurConsignes)/100)
            if (abs(valeurCouranteTension - TensionConsigneEnregistree) > abs(ErreurCourante)) :
#                 ErreurCourante = ((TensionConsigne*PourcentErrSurConsignes)/100)
                valeurCouranteTension, ErreurEnregistree = regulationTension(TensionConsigne, abs(ErreurCourante))
#                 print()
#                 print("mise à jour de la regulation de tension à '", str(TensionConsigne), "' mV en mode :", str(mode_de_test))
#                 print("erreur enregistrée : ", str(ErreurEnregistree), " mV sur consigne :", str(TensionConsigne), " mV")
#                 print("-> derniereValeurResistanceAppliquee " +str(derniereValeurResistanceAppliquee))

        LectureEntreeEtMiseAJour()
        
        if((datetime.datetime.now().timestamp() - LocalDateEnregistrementBD.timestamp()) > tempsEnregistrementBD ) :
            try:
                connection = sqlite3.connect("database.db")
                cursor = connection.cursor()             
                new_record = (cursor.lastrowid, numero_courant_enregistrement, Date, round(valeurCouranteTension), round(valeurCouranteCourant),
                              round(ErreurCourante), round((tensionET-tensionEREF)), mode_de_test, mode_de_branchement) #definition de l'enregisstrement. peut être définit sous forme de liste
#                 print(new_record)
                cursor.execute('INSERT INTO mesures VALUES(?,?,?,?,?,?,?,?,?)', new_record)
                connection.commit() # toujours valider l'enregistrement
                
                rec = (numero_courant_enregistrement,)
                result = cursor.execute('SELECT date FROM mesures WHERE numero_test = ?', rec)
                lesdates = result.fetchall()
                result = cursor.execute('SELECT differentiel FROM mesures WHERE numero_test = ?', rec)
                lestensions  = result.fetchall()
#                 print(lestensions)
                result = cursor.execute('SELECT courant FROM mesures WHERE numero_test = ?', rec)
                lescourants  = result.fetchall()
#                 print(lescourants)
                
                ax1.clear()
                if (TypeDeGraphique ==1):
                    laliste =[]
                    for i in range(len(lesdates)) :
                       laliste.append(lesdates[i][0])
#                     print(laliste)
                    times = pd.DatetimeIndex(laliste)
#                     print(times)
                    fig.autofmt_xdate()
                    ax1.set_ylim( 0,len(lescourants),auto=True) 
                    ax1.set_xlim( 0,len(laliste), auto=True)
                    ax1.set_ylabel('courant (mA)', color='r')            
                    ax1.set_xlabel('temps (s)', color='g')
                    xfmt = mdates.DateFormatter('%d/%m/%y %H:%M:%S')
                    ax1.xaxis.set_major_formatter(xfmt)
                    ax1.plot(times, lescourants, 'g-o')                
                elif (TypeDeGraphique ==2):
                    ax1.set_ylim( 0,len(lestensions) , auto=True)
                    ax1.set_xlim( 0,len(lescourants), auto=True)
                    ax1.set_ylabel('tension differentielle (mV)', color='g')
                    ax1.set_xlabel('courant (mA)', color='r')
                    ax1.plot(lescourants, lestensions, 'g-o')

            except Exception as e:
                connection.rollback() #faire un retour en arrière par rapporrt à une requette qui s'est mal passée  
#                 print("[ERREUR SUR LA BD] : ", e)
            finally:
                connection.close()
#                 print("close")
                
            LocalDateEnregistrementBD =  datetime.datetime.now()                                                  
#    else :
#         print("pas de test en cours !")
    
def ActionButtonTC():
    print()
    print("ActionButtonTC()") 
    TestEnCours = MessageTestEnCours()
    if TestEnCours == 0:
        button_tc['state'] = tk.DISABLED
        button_cc['state'] = tk.NORMAL
        listeCombTension['state'] ='normal'        #readonly or normal
        listeCombCourant['state'] ='disabled'
        sortieTension['state'] ='normal'
        sortieCourant['state'] ='disabled'
        sortieErrTension['state'] = 'normal'
        sortieErrCourant['state'] = 'disabled'
        mode_tc_cc=0
        print("mode_tc_cc: " + str(mode_tc_cc) + " => Tension Constante")

def ActionButtonCC():
    print()
    print("ActionButtonCC()")
    TestEnCours = MessageTestEnCours()
    if TestEnCours == 0:
        button_cc['state'] = tk.DISABLED
        button_tc['state'] = tk.NORMAL
        listeCombCourant['state'] ='normal' #readonly or normal   
        listeCombTension['state'] ='disabled'
        sortieCourant['state'] ='normal'
        sortieTension['state'] ='disabled'
        sortieErrCourant['state'] = 'normal'
        sortieErrTension['state'] = 'disabled'
        mode_tc_cc=1 
        print("mode_tc_cc: " + str(mode_tc_cc) + " => Courant Constant")

def ActionButtonPConstant():
    print()
    print("ActionButtonPConstant()")
    TestEnCours = MessageTestEnCours()
    if TestEnCours == 0:
        button_pconstant['state'] = tk.DISABLED
        button_pcontrole['state'] = tk.NORMAL
        DelaisIncrPControle['state'] ='disabled'
        listeCombCourant['state'] ='disabled'
        sortieCourant['state'] ='disabled'
        sortieErrCourant['state'] = 'disabled'
        listeCombTension['state'] ='disabled' #readonly or normal
        sortieTension['state'] ='disabled'
        sortieErrTension['state'] = 'disabled'
        global mode_pc_pc
        global mode_tc_cc
        global mode_pc_t_c
        mode_tc_cc = mode_pc_t_c
        if mode_tc_cc > 0:
            listeCombCourant['state'] ='normal'
            sortieCourant['state'] ='normal'
            sortieErrCourant['state'] = 'normal'
            print("mode_tc_cc " + str(mode_tc_cc) +" => *Potentiel Constant en courant*")
        else :
            listeCombTension['state'] ='normal' #readonly or normal
            sortieTension['state'] ='normal'
            sortieErrTension['state'] = 'normal'
            print("mode_tc_cc " + str(mode_tc_cc) +" => *Potentiel Constant en Tension*")   
        mode_pc_pc=0
        print("mode_pc_pc: " + str(mode_pc_pc) + " => Potentiel Constant")

def ActionButtonPControle():
    print()
    print("ActionButtonPControle()")
    TestEnCours = MessageTestEnCours()
    if TestEnCours == 0:
        button_pcontrole['state'] = tk.DISABLED
        button_pconstant['state'] = tk.NORMAL
        DelaisIncrPControle['state'] ='normal'
        listeCombCourant['state'] ='disabled'
        sortieCourant['state'] ='disabled'
        sortieErrCourant['state'] = 'disabled'
        listeCombTension['state'] ='disabled' #readonly or normal
        sortieTension['state'] ='disabled'
        sortieErrTension['state'] = 'disabled'
        global mode_pc_pc
        global mode_pc_t_c
        global mode_tc_cc
        mode_pc_t_c = mode_tc_cc
        if mode_pc_t_c > 0 :
            listeCombCourant['state'] ='normal'
            sortieCourant['state'] ='normal'
            sortieErrCourant['state'] = 'normal'
            print("mode_pc_t_c " + str(mode_pc_t_c) + " => *Potentiel Controlé en courant*")
#             listeCombCPcontrole['state'] ='normal' #readonly or normal
#             listeCombTPcontrole['state'] ='disabled' #readonly or normal
        else :
            listeCombTension['state'] ='normal' #readonly or normal
            sortieTension['state'] ='normal'
            sortieErrTension['state'] = 'normal'
            print("mode_pc_t_c " + str(mode_pc_t_c) +" => *Potentiel Controlé en tension*")
#             listeCombCPcontrole['state'] ='disabled' #readonly or normal
#             listeCombTPcontrole['state'] ='normal' #readonly or normal
        mode_pc_pc =1  
        print("mode_pc_pc: " + str(mode_pc_pc) + " => Potentiel Controlé")

def ActionButtonTension():
    print()
    print("ActionButtonTension()")
    TestEnCours = MessageTestEnCours()
    if TestEnCours == 0:
        global mode_pc_pc
        global mode_pc_t_c
        global mode_tc_cc
        
        ButtonTension['state'] = 'disabled'
        ButtonCourant['state'] = 'normal'
        listeCombCourant['state'] ='disabled'
        sortieCourant['state'] ='disabled'
        sortieErrCourant['state'] = 'disabled' 
        listeCombTension['state'] ='normal' #readonly or normal
        sortieTension['state'] ='normal'
        sortieErrTension['state'] = 'normal'

        if mode_pc_pc > 0 :  # le mode de fonctionnement est le potentiel controlé
            DelaisIncrPControle['state'] ='normal'
            mode_pc_t_c=0
            print("mode_pc_t_c: " + str(mode_pc_t_c) + " => Potentiel Controlé en tension")
        else: #le mode de fonctionnement est le potentiel constant
            DelaisIncrPControle['state'] ='disabled'
            mode_tc_cc=0
            print("mode_tc_cc: " + str(mode_tc_cc) + " => Potentiel constant en tension")

def ActionButtonCourant():
    print()
    print("ActionButtonCourant()")
    TestEnCours = MessageTestEnCours()
    if TestEnCours == 0:
        ButtonTension['state'] = 'normal'
        ButtonCourant['state'] = 'disabled'
        listeCombTension['state'] ='disabled' #readonly or normal
        sortieTension['state'] ='disabled'
        sortieErrTension['state'] = 'disabled'
        listeCombCourant['state'] ='normal'
        sortieCourant['state'] ='normal'
        sortieErrCourant['state'] = 'normal' 
        global mode_pc_pc
        global mode_pc_t_c
        global mode_tc_cc
        if mode_pc_pc > 0 :  # le mode de fonctionnement est le potentiel controlé
            DelaisIncrPControle['state'] ='normal'
            mode_pc_t_c=1
            print("mode_pc_t_c: " + str(mode_pc_t_c) + " => Potentiel Controlé en courant")
        else: #le mode de fonctionnement est le potentiel constant
            DelaisIncrPControle['state'] ='disabled'
            mode_tc_cc=1
            print("mode_tc_cc: " + str(mode_tc_cc) + " => Potentiel constant en courant")

def actionlisteTPcontrole(event):
    print()
    print("actionlisteTPcontrole()")
    select = listeCombTPcontrole.get()
    print("Vous avez sélectionné : '", select,"'")

def actionlisteCPcontrole(event):
    print()
    print("actionlisteCPcontrole()")
    select = listeCombCPcontrole.get()
    print("Vous avez sélectionné : '", select,"'")

def ActionButtonBN():
    print()
    print("ActionButtonBN()")
    TestEnCours = MessageTestEnCours()
    if TestEnCours == 0:
        button_bn['state'] = tk.DISABLED
        button_bi['state'] = tk.NORMAL
        global mode_de_branchement
        mode_de_branchement=0
        print("mode_de_branchement: " + str(mode_de_branchement) + " => Branchement Normal")

def ActionButtonBI():
    print()
    print("ActionButtonBI()")
    TestEnCours = MessageTestEnCours()
    if TestEnCours == 0:
        button_bi['state'] = tk.DISABLED
        button_bn['state'] = tk.NORMAL
        mode_de_branchement=1
        print("mode_de_branchement: " + str(mode_de_branchement) + " => Branchement Inverse")

def actionlisteTC(event):
    print()
    print("actionlisteTC()")
    # Obtenir l'élément sélectionné
    select = listeCombTension.get()
    print("Vous avez sélectionné : '", select,"'")
    
def actionlisteCC(event):
    print()
    print("actionlisteCC()")
    # Obtenir l'élément sélectionné
    select = listeCombCourant.get()
    print("Vous avez sélectionné : '", select,"'")
    
def actionlisteDureeTest(event) :
    print()
    print("actionlisteDureeTest()")
    # Obtenir l'élément sélectionné
    select = listeCombDureeTest.get()
    print("Vous avez sélectionné : '", select,"'")
    
def actionlisteDureeEnregistrement(event) :
    global tempsEnregistrementBD
    print()
    print("actionlisteDureeTest()")
    # Obtenir l'élément sélectionné
    select = listeCombDureeEnregistrement.get()
    print("Vous avez sélectionné : '", select,"'")
    tempsEnregistrementBD = int(select[:-1])
    print("tempsEnregistrementBD" + str(tempsEnregistrementBD) + "s")
    
def vitesse_moteur(event):
    print()
    print("vitesse_moteur()")
    TestEnCours = MessageTestEnCours()
    if TestEnCours == 1:
        x=echellePwm.get()
        Pwm0.value=x
        if (x == 0) :
           Pwm0.value = 0.5 # ne pas completement arreter le moteur lorsqu'un test est en cours 
        print("echelle: " + str(x))

def ActionButtonM():
    print()
    print("ActionButtonM()")
    BoutonMarche['state'] = tk.DISABLED
    BoutonArret['state'] = tk.NORMAL
    sortieDateDebut.delete(0, tk.END)
    sortieDateFin.delete(0, tk.END)
    buttonAfficher['state'] = tk.DISABLED
    sortieET.delete(0, tk.END)
    sortieEREF.delete(0, tk.END)
    sortieCE.delete(0, tk.END)
    sortieCourant.delete(0, tk.END)
    sortieTension.delete(0, tk.END)
    sortieErrTension.delete(0, tk.END)
    sortieErrCourant.delete(0, tk.END)
    ax1.clear()
    
    global TensionConsigneEnregistree
    global TensionConsigne
    global CourantConsigneEnregistree
    global CourantConsigne
    global ErreurCourante
    global ErreurEnregistree
    global DureeDuTestEnregistree
    global DelaisIncrConsigneEnregistree
    global CptrDelaisIncrConsigne
    global pulsee
    global DateDebutTest
    global LocalDateDebutTest
    global LocalDateIncrConsigne      
    global LocalDateEnregistrementBD    
    global tempsEnregistrementBD
    global derniereValeurResistanceAppliquee
    derniereValeurResistanceAppliquee = 0
    #enregistrement des consignes
    select = listeCombTension.get()
    TensionConsigneEnregistree = int(select[:-3])         #extraction du nombre dans la liste
    TensionConsigne = TensionConsigneEnregistree
    print("TensionConsigneEnregistree : ", str(TensionConsigneEnregistree), " *mV")
    print("TensionConsigne : ", str(TensionConsigne), " *mV")
    
    select = listeCombCourant.get()
    CourantConsigneEnregistree = int(select[:-3])         #extraction du nombre dans la liste
    CourantConsigne = CourantConsigneEnregistree
    print("CourantConsigneEnregistree : ", str(CourantConsigneEnregistree), " *mA")
    print("CourantConsigne : ", str(CourantConsigne), " *mA")
    
    select = listeCombDureeTest.get()
    DureeDuTestEnregistree  = int(select[:-3]) * 60                          #extraction du nombre et conversion en secondes pour le mode à Potentiel controlé 
    print("DureeDuTestEnregistree : ", str(DureeDuTestEnregistree), " *min")
    
    select = DelaisIncrPControle.get()
    DelaisIncrConsigneEnregistree = int(select)
    print("DelaisIncrConsigneEnregistree : ", str(DelaisIncrConsigneEnregistree), " *s")

    select = listeCombDureeEnregistrement.get()
    tempsEnregistrementBD = int(select[:-1])
    print("tempsEnregistrementBD : ", str(tempsEnregistrementBD), " *s")
    
    global mode_marche_arret
    global mode_de_test
    global mode_pc_pc
    global mode_tc_cc
    global mode_pc_t_c
    #definition du mode de test
    # faire une première regulation en courant ou en tension selon le cas
    if (mode_pc_pc == 1) : # test si mode potensiel controlé
        if (mode_pc_t_c > 0) : #test si mode potentiel controlé en courant
            mode_de_test =3
        else : #mode potentiel controlé en tension 
            mode_de_test =2 
    elif (mode_pc_pc == 0) : # mode potentiel constant
        if (mode_tc_cc > 0) : # test si mode potentiel contant en courant
            mode_de_test =1
        else :  #mode potentiel constant en tension
            mode_de_test =0
        
    pulsee =0               # réinitialiser le compteur sur la durée du test  
    Potentiometre.on()
    Pwm0.value = 0.5
    echellePwm.set(0.5)
    mode_marche_arret =1
    
    #première regulation
    if (mode_de_test == 1 or mode_de_test == 3 ) :
        ErreurCourante = (CourantConsigneEnregistree*PourcentErrSurConsignes)/100
        valeurCouranteCourant, ErreurEnregistree = regulationCourant(CourantConsigneEnregistree, ErreurCourante)
        print("*première regulation Courant*")
    
    elif (mode_de_test == 0 or mode_de_test == 2 ) :
        ErreurCourante = (TensionConsigneEnregistree*PourcentErrSurConsignes)/100   
        ValeurCouranteTension, ErreurEnregistree = regulationTension(TensionConsigneEnregistree, ErreurCourante)        
        print("*première regulation Tension*")
        print("ErreurCourante", str(ErreurCourante))
        print("ValeurCouranteTension", str(ValeurCouranteTension), "erreur save", str(ErreurEnregistree) )
    
    LocalDateDebutTest        = datetime.datetime.now()
    LocalDateIncrConsigne     = LocalDateDebutTest 
    LocalDateEnregistrementBD = LocalDateDebutTest
    DateDebutTest = lectureHorloge()
    sortieTempsD.delete(0, tk.END)
    sortieTempsD.insert(0, DateDebutTest)
    sortieTempsF.delete(0, tk.END)
    print("Horloge de debut du test : ", DateDebutTest)
    print("mode_de_test: " + str(mode_de_test))
    print("mode_marche_arret: " + str(mode_marche_arret) + " => Demmarage du test") 
 
def ActionButtonA():
    print()
    print("ActionButtonA()")
    global nombreTestsBD
    global numero_courant_enregistrement
    global derniereValeurResistanceAppliquee
    derniereValeurResistanceAppliquee = 0

    BoutonArret['state'] = tk.DISABLED
    BoutonMarche['state'] = tk.NORMAL
    enregistrements =0
    try:
        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()  
        result = cursor.execute('SELECT date FROM mesures WHERE numero_test = ?', (numero_courant_enregistrement,))
        lesdates = result.fetchall()
#         print(len(lesdates))
        enregistrements = len(lesdates)   
    except Exception as e:
        connection.rollback() #faire un retour en arrière par rapporrt à une requette qui s'est mal passée
#         print("[ERREUR SUR LA BD] : ", e)   
    finally:
        connection.close()
            
    if(enregistrements > 0) : 
        buttonAfficher['state'] = tk.NORMAL
        listeCombEnregistrements['state'] =tk.NORMAL
        liste=[]
        for i in range(nombreTestsBD + 1 ) :
           liste.append(i+1)
           
        listeCombEnregistrements['values'] =liste
#         print("nouvelle liste :", liste)
        nombreTestsBD +=1
        numero_courant_enregistrement +=1
        
    elif nombreTestsBD > 0:
        buttonAfficher['state'] = tk.NORMAL
        
    else :
        buttonAfficher['state'] = tk.DISABLED
    
    global mode_marche_arret
    global pulsee
    global DateFinTest
    DateFinTest = lectureHorloge()
    sortieTempsF.delete(0, tk.END)
    sortieTempsF.insert(0, DateFinTest)
    pulsee =0
    Ecriture_ad5241(0x00, [0x00])  #remettre la tension ou le courant à 0 selon le mode de fonctionnement   
    echellePwm.set(0)
    Pwm0.value =0
    Potentiometre.off()
    mode_marche_arret =0
#     print("mode_marche_arret: " + str(mode_marche_arret) + " => Arret du test")  

def actionlisteTypeGraph(event):
    print()
    print("(actionlisteTypeGraph()")
    global TypeDeGraphique
    select = listeCombTypeGraphique.get()
    TypeDeGraphique = int(select)
    print("Vous avez sélectionné : '", select,"'")
    print("Type de graphique selectionné : " + str(TypeDeGraphique))

def actionlisteEnregistrement(event):
    print()
    print("(actionlisteEnregistrement()")
    global numero_enregistrement_a_afficher
    # Obtenir l'élément sélectionné
    TestEnCours = MessageTestEnCours()
    if TestEnCours == 0:
        buttonAfficher['state'] = tk.NORMAL
        select = listeCombEnregistrements.get()
        numero_enregistrement_a_afficher = int(select)
        print("Vous avez sélectionné : '", select,"'")
        print("Vous avez sélectionné l'enregistrement N:" + str(numero_enregistrement_a_afficher))
    
def ActionButtonAfficher():
    print()
    print("ActionButtonAfficher()")
    global numero_enregistrement_a_afficher
    global TypeDeGraphique
    #demander à l'utilisateur s'il souhaite arreter le test en cours s'il y en a un
    #lire les données correspondants à l'enregistrement selectionné et les afficher  

    TestEnCours = MessageTestEnCours()
    if TestEnCours == 0:
        #fonction : afficherMesures(numeroEnre
        sortieET.delete(0, tk.END)
        sortieEREF.delete(0, tk.END)
        sortieCE.delete(0, tk.END)
        sortieCourant.delete(0, tk.END)
        sortieTension.delete(0, tk.END)
        sortieErrTension.delete(0, tk.END)
        sortieErrCourant.delete(0, tk.END)    
        sortieCourantTest.delete(0, tk.END)
        sortieTempsF.delete(0, tk.END)
        sortieTempsD.delete(0, tk.END)
        select = listeCombEnregistrements.get()
        numero_enregistrement_a_afficher = int(select)
#         print("Le numéro de l'enregistrement est : " + str(numero_enregistrement_a_afficher))
        try:
            connection = sqlite3.connect("database.db")
            cursor = connection.cursor()
            
            rec = (numero_enregistrement_a_afficher,)
            result = cursor.execute('SELECT date FROM mesures WHERE numero_test = ?', rec)
            lesdates = result.fetchall()
#             print(lesdates)
            premier = lesdates[0][0]
#             print(premier)
            dernier = lesdates[-1][0]
#             print(dernier)
            sortieDateDebut.delete(0, tk.END)
            sortieDateDebut.insert(0, premier)
            sortieDateFin.delete(0, tk.END)
            sortieDateFin.insert(0, dernier)
            result = cursor.execute('SELECT differentiel FROM mesures WHERE numero_test = ?', rec)
            lestensions  = result.fetchall()
#             print(lestensions)
            result = cursor.execute('SELECT courant FROM mesures WHERE numero_test = ?', rec)
            lescourants  = result.fetchall()
#             print(lescourants)
            ax1.clear()
            if (TypeDeGraphique ==1):
                laliste =[]
                for i in range(len(lesdates)) :
                   laliste.append(lesdates[i][0])
#                 print(laliste)
                times = pd.DatetimeIndex(laliste)
#                 print(times)
                fig.autofmt_xdate()
#                 ax1.set_ylim( 0,len(lescourants),auto=True) 
#                 ax1.set_xlim( 0,len(laliste), auto=True)
#                 ax1.xaxis.set_ticks(np.arange(0, len(laliste), 1))
                ax1.set_ylabel('courant (mA)', color='r')            
                ax1.set_xlabel('temps (s)', color='g')
                xfmt = mdates.DateFormatter('%d/%m/%y %H:%M:%S')
                ax1.xaxis.set_major_formatter(xfmt)
                ax1.plot(times, lescourants, 'g-o')
            
            elif (TypeDeGraphique ==2):
                ax1.set_ylim( 0,len(lestensions), auto=True)
                ax1.set_xlim( 0,len(lescourants),auto=True ) 
                ax1.set_ylabel('tension differentielle (mV)', color='g')
                ax1.set_xlabel('courant (mA)', color='r')                
                ax1.plot(lescourants, lestensions, 'g-o')
        except Exception as e:
            connection.rollback() #faire un retour en arrière par rapporrt à une requette qui s'est mal passée  
#             print("[ERREUR SUR LA BD] : ", e)
        finally:
            connection.close()    
        
fen = tk.Tk()                             #intanciation ou creation d'un objet fenêtre graphique
fen.title("Tests Electrogravimetrie / Coulometrie")  #definition du titre de la fenêtre 

frame11 = tk.Frame(fen) #boite permettant de center les entités : bouton, echelles etc. 
frame11.pack(side=tk.LEFT,padx=decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre

frame12 = tk.Frame(fen) #boite permettant de center les entités : bouton, echelles etc. 
frame12.pack(side=tk.RIGHT, padx=decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre

#comment definir le demarrage de l'applicquation centré par rapport à l'écran ?
#fen.update() # Suivant le WM. A faire dans tous les cas donc.
#fenrw = 800 #fen.winfo_reqwidth()
#fenrh = 650 #fen.winfo_reqheight()
#sw = fen.winfo_screenwidth()
#sh = fen.winfo_screenheight()
#print(fenrw, fenrh, sw, sh)
#fen.geometry("%dx%d+%d+%d" % (fenrw, fenrh, (sw-fenrw)/2, (sh-fenrh)/2))
#fen.geometry("900x640")   #definition des dimensions de la fenêtre 
#fen.minsize(800, 600)     #fixer la taille minimale de la fenêtre pour le redimentionnement manuel
#fen.config(background="white") #definir une couleur de fond de le fenêtre

#frame = tk.Frame(fen, bg='#C9C3AB') #boite permettant de center les entités : bouton, echelles etc.
#frame.pack() 
#frame.pack(expand=tk.YES)  #'expand=YES' pour permettre aux entités de s'adapter au redimentionnement de la fenetre 
#quand on crée la frame, mettre les boutons à l'intérieur 

frame1 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
frame1.pack(pady = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame1)
labelChoix_tc = tk.Label(frame1, text = "Durée du test:")
labelChoix_tc.pack(side = tk.LEFT, padx = decallagex)

#créer la liste Python contenant les éléments de la liste Combobox
listeDureeTest=["1 min", "2 min", "3 min", "4 min", "5 min", "10 min", "20 min","30 min","40 mim",
                "50 min","60 min","70 min", "80 min", "90 min", "100 min", "110 min", "120 min"]
#Création de la Combobox via la méthode ttk.Combobox()
listeCombDureeTest = ttk.Combobox(frame1, values=listeDureeTest, state='normal', width=LongeurConsignes)
# 4) - Choisir l'élément qui s'affiche par défaut
listeCombDureeTest.current(0)
listeCombDureeTest.pack(side = tk.LEFT,  padx = decallagex)
listeCombDureeTest.bind("<<ComboboxSelected>>", actionlisteDureeTest)

labelChoix_tc = tk.Label(frame1, text = "Temps Enregistrement:")
labelChoix_tc.pack(side = tk.LEFT, padx = decallagex)
listeDureeEnregistrement=["1 s", "2 s", "3 s", "4 s", "5 s","6 s","7 s","8 s","9 s","10 s","11 s","12 s","13 s","14 s","15 s","16 s",
                          "17 s","18 s","19 s","20 s", "21 s", "22 s","23 s","24 s","25 s", "26 s","27 s","28 s","29 s","30 s"]
listeCombDureeEnregistrement = ttk.Combobox(frame1, values=listeDureeEnregistrement, state='normal', width=LongeurConsignes)
listeCombDureeEnregistrement.current(1)
listeCombDureeEnregistrement.pack(side = tk.LEFT)
listeCombDureeEnregistrement.bind("<<ComboboxSelected>>", actionlisteDureeEnregistrement)

frame1 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
frame1.pack(pady = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame1)
labelChoix_modef = tk.Label(frame1, text = "Choix du mode de fonctionnement:")
labelChoix_modef.pack(pady = decallagex)
button_pconstant = tk.Button(frame1, text="POTENTIEL CONSTANT", command=ActionButtonPConstant, state=tk.DISABLED)
button_pconstant.pack(side=tk.LEFT, padx = decallagex)
button_pcontrole = tk.Button(frame1, text="POTENTIEL CONTROLE", command=ActionButtonPControle)
button_pcontrole.pack(side=tk.LEFT, padx = decallagex)

frame2 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
frame2.pack(pady = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame2)
labelChoixPcontrole = tk.Label(frame2, text = "Choix du mode de commande:")
labelChoixPcontrole.pack(pady = decallagex)
#frame1 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
#frame1.pack() #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
ButtonTension = tk.Button(frame2, text="TENSION", command=ActionButtonTension, state=tk.DISABLED)
ButtonTension.pack(side=tk.LEFT)
ButtonCourant = tk.Button(frame2, text="COURANT", command=ActionButtonCourant)
ButtonCourant.pack(side=tk.RIGHT)

# frame1 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
# frame1.pack() #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
# frames_boutons.append(frame1)
# labelChoixPcontrole = tk.Label(frame1, text = "Delta Tension (mV):             Delta courant (mA):              temps (s)")
# labelChoixPcontrole.pack()
# #créer la liste Python contenant les éléments de la liste Combobox
# listeTensionsPcontrole=["0 mV", "100 mV","200 mV","300 mV", "400 mV","500 mV","600 mV", "700 mV", "800 mV", "900 mV", "1000 mV"]
# #Création de la Combobox via la méthode ttk.Combobox()
# listeCombTPcontrole = ttk.Combobox(frame1, values=listeTensionsPcontrole, state='disabled')
# listeCombTPcontrole.current(0) # 4) - Choisir l'élément qui s'affiche par défaut
# listeCombTPcontrole.pack(side = tk.LEFT)
# listeCombTPcontrole.bind("<<ComboboxSelected>>", actionlisteTPcontrole)
# 
# listeCourantsPcontrole=["0mA", "100 mA","200 mA","300 mA","400 mA","500 mA","600 mA", "700 mA", "800 mA", "900 mA", "1000 mA"]
# listeCombCPcontrole = ttk.Combobox(frame1, values=listeCourantsPcontrole, state='disabled')
# listeCombCPcontrole.current(0)
# listeCombCPcontrole.pack(side = tk.LEFT)
# listeCombCPcontrole.bind("<<ComboboxSelected>>", actionlisteCPcontrole)

# frame1 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
# frame1.pack() #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
# frames_boutons.append(frame1)
# labelChoix_modef = tk.Label(frame1, text = "choix du mode de fonctionnement en potentiel constant:")
# labelChoix_modef.pack()
# #labelChoix_modef.pack(side=tk.LEFT, pady=5 )
# button_tc = tk.Button(frame1, text="TENSION CONSTANTE", command=ActionButtonTC, state=tk.DISABLED)
# button_tc.pack(side=tk.LEFT)
# #button_tc.pack(side=tk.LEFT,pady=5)
# button_cc = tk.Button(frame1, text="COURANT CONSTANT", command=ActionButtonCC)
# button_cc.pack(side=tk.LEFT)
#button_cc.pack(side=tk.LEFT)
#button_cc.pack(side=tk.LEFT)

frame3 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
frame3.pack(pady = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame3)
labelChoix_tc = tk.Label(frame3, text = "   Consignes    ")
labelChoix_tc.pack(pady = decallagex)
labelChoix_tc = tk.Label(frame3, text = "Tension (mV):     Courant (mA):     Delais (s):")
labelChoix_tc.pack(pady = decallagex)
#créer la liste Python contenant les éléments de la liste Combobox
listeTension=["50 mV", "100 mV","150 mV","200 mV", "250 mV","300 mV","350 mV", "400 mV", "450 mV", "500 mV", "550 mV",  "600 mV",  "650 mV",
              "700 mV","750 mV", "800 mV","850 mV","900 mV", "950 mV","1000 mV","1050 mV", "1100 mV", "1150 mV", "1200 mV", "1250 mV",
              "1300 mV",  "1350 mV","1400 mV", "1450 mV","1500 mV","1550 mV", "1600 mV","1650 mV","1700 mV", "1750 mV", "1800 mV", "1850 mV",
              "1900 mV",  "1950 mV",  "2000 mV","2050 mV", "2100 mV","2150 mV","2200 mV", "2250 mV","2300 mV","2350 mV", "2400 mV", "2450 mV",
              "2500 mV", "2550 mV",  "2600 mV",  "2650 mV","2700 mV", "2750 mV","2800 mV","2850 mV", "2900 mV","2950 mV","3000 mV"]
#Création de la Combobox via la méthode ttk.Combobox()
listeCombTension = ttk.Combobox(frame3, values=listeTension, state='normal', width=LongeurEntreesSorties)
# 4) - Choisir l'élément qui s'affiche par défaut
listeCombTension.current(0)
listeCombTension.pack(side = tk.LEFT, padx = decallagex)
listeCombTension.bind("<<ComboboxSelected>>", actionlisteTC)
#labelChoix_cc = tk.Label(frame1, text = "Courant de consigne (mA):")
#labelChoix_cc.pack()
#créer la liste Python contenant les éléments de la liste Combobox
listeCourant=["50 mA", "100 mA","150 mA","200 mA", "250 mA","300 mA","350 mA", "400 mA", "450 mA", "500 mA",
              "550 mA", "600 mA", "650 mA","700 mA","750 mA", "800 mA","850 mA", "900 mA","950 mA","1000 mA"]
#Création de la Combobox via la méthode ttk.Combobox()
listeCombCourant = ttk.Combobox(frame3, values=listeCourant, state='disabled', width=LongeurEntreesSorties)
# 4) - Choisir l'élément qui s'affiche par défaut
listeCombCourant.current(0)
listeCombCourant.pack(side = tk.LEFT, padx = decallagex)
listeCombCourant.bind("<<ComboboxSelected>>", actionlisteCC)

DelaisIncrPControle = tk.Entry(frame3, width=LongeurEntreesSorties)
DelaisIncrPControle.pack(side =tk.LEFT)
DelaisIncrPControle['state']='normal'
DelaisIncrPControle.insert(0, 1)
DelaisIncrPControle['state']='disabled'

frame4 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
frame4.pack(pady = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame4)
labeltc = tk.Label(frame4, text = "Sorties ")
labeltc.pack(pady = decallagex)
labeltc = tk.Label(frame4, text = "Tension (mV):    Courant (mA):")
labeltc.pack(pady = decallagex)
sortieTension = tk.Entry(frame4, width=LongeurEntreesSorties)
sortieTension.pack(side =tk.LEFT, padx = decallagex)
sortieTension.insert(0, 0)
#labelcc = tk.Label(frame1, text = "Courant de sortie (mA):")
#labelcc.pack()
sortieCourant = tk.Entry(frame4,  state='disabled', width=LongeurEntreesSorties)
sortieCourant.pack(side = tk.LEFT)
sortieCourant['state']='normal'
sortieCourant.insert(0, 0)
sortieCourant['state']='disabled'

frame5 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
frame5.pack(pady = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame5)
labelErrTension = tk.Label(frame5, text = "Erreurs")
labelErrTension.pack(pady = decallagex)
labelErrTension = tk.Label(frame5, text = "Tension (mV) :     Courant (mA) :")
labelErrTension.pack(pady = decallagex)
sortieErrTension = tk.Entry(frame5, width=LongeurEntreesSorties)
sortieErrTension.pack(side = tk.LEFT, padx = decallagex)
sortieErrTension.insert(0, 0)
#labelErcc = tk.Label(frame1, text = "Erreur Courant de sortie (mA):")
#labelErcc.pack()
sortieErrCourant = tk.Entry(frame5,  state='disabled', width=LongeurEntreesSorties)
sortieErrCourant.pack(side = tk.LEFT)
sortieErrCourant['state']='normal'
sortieErrCourant.insert(0, 0)
sortieErrCourant['state']='disabled'

frame2 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
frame2.pack(pady = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame2)
labelChoix_modeb = tk.Label(frame2, text = "Choix du mode de branchement des électrodes :")
labelChoix_modeb.pack(pady = decallagex)
#labelChoix_modeb.pack(side=tk.LEFT)
button_bn = tk.Button(frame2, text="BRANCHEMENT NORMALE", command=ActionButtonBN, state=tk.DISABLED)
button_bn.pack(side=tk.LEFT, padx = decallagex)
#button_bn.pack(side=tk.LEFT, pady=5)
#button_bn.pack(side=tk.LEFT)
button_bi = tk.Button(frame2, text="BRANCHEMENT INVERSE", command=ActionButtonBI)
button_bi.pack(side = tk.LEFT, padx = decallagex)
#button_bi.pack(side=tk.LEFT, pady=5)
#button_bi.pack(side=tk.LEFT)

frame6 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
frame6.pack(pady = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame6)
# labelvm = tk.Label(frame6, text = "Vitesse du moteur (%) :")
# labelvm.pack()
#echelle de commande de la LED en PWM echelle de 0 à 1
echellePwm = tk.Scale(frame6,from_=0,to=1,orient=tk.HORIZONTAL,
                resolution=0.1, tickinterval=0.1, length=400,
                label='Vitesse du moteur (%):',
                command=vitesse_moteur) #bg='white',fg='#C9C3AB'
echellePwm.set(0)
echellePwm.pack()
Pwm0.value=0

frame7 = tk.Frame(frame11) #boite permettant de center les entités : bouton, echelles etc. 
frame7.pack(pady = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame7)
label_marche = tk.Label(frame7, text = "Mettre en Marche         Mettre à l'arret")
label_marche.pack(padx = decallagex)
BoutonMarche = tk.Button(frame7, text="LANCER LE TEST", command=ActionButtonM)
BoutonMarche.pack(side = tk.LEFT, padx = decallagex)
#label_arret = tk.Label(frame1, text = "Mise à l'Arret")
#label_arret.pack()
BoutonArret = tk.Button(frame7, text="ARRETER LE TEST", command=ActionButtonA, state=tk.DISABLED)
BoutonArret.pack(side = tk.LEFT)

#curseurPwm.pack(pady=5, fill=X) #creer un ecartement  entre les entités de la frame 
#bouton_cv_cc.pack(pady=5, fill=X) #creer un ecartement  entre les entités de la frame 
#anifunc = FuncAnimation(fig, update_graph, interval=2000)

frame8 = tk.Frame(frame12) #boite permettant de center les entités : bouton, echelles etc. 
frame8.pack(pady = decallagex) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame8)
labelDate = tk.Label(frame8, text = "Date:")
labelDate.pack(side = tk.LEFT, padx=decallagex)
sortieDate = tk.Entry(frame8,  state='normal', width=17)
sortieDate.pack(side=tk.LEFT, padx =decallagex)

labelTypeGraph = tk.Label(frame8, text = " Selection du Type de Graphique:")
labelTypeGraph.pack(side = tk.LEFT, padx = decallagex)
listeTypeGraphique=["1", "2"]
listeCombTypeGraphique = ttk.Combobox(frame8, values=listeTypeGraphique, state='normal', width=LongeurConsignes)
listeCombTypeGraphique.current(0)
listeCombTypeGraphique.pack(side = tk.LEFT, padx = decallagex)
listeCombTypeGraphique.bind("<<ComboboxSelected>>", actionlisteTypeGraph)

frame8 = tk.Frame(frame12) #boite permettant de center les entités : bouton, echelles etc. 
frame8.pack(pady = decallagex) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame8)
labelTempsD = tk.Label(frame8, text = "Heure Début:")
labelTempsD.pack(side=tk.LEFT, padx = decallagex)
sortieTempsD = tk.Entry(frame8,  state='normal', width=17)
sortieTempsD.pack(side=tk.LEFT, padx = decallagex)
labelTempsD = tk.Label(frame8, text = "Heure Fin:")
labelTempsD.pack(side=tk.LEFT, padx = decallagex)
sortieTempsF = tk.Entry(frame8,  state = 'normal', width=17)
sortieTempsF.pack(side=tk.LEFT, padx=decallagex)

frame9 = tk.Frame(frame12) #boite permettant de center les entités : bouton, echelles etc. 
frame9.pack(pady = decallagex) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame9)

style.use("ggplot")
#fig = Figure(figsize=(6, 4), dpi=110)
fig = Figure(figsize=(8, 6), dpi=70)
# fig.autofmt_xdate()
ax1 = fig.add_subplot(1,1,1)
# print(type(fig))
# print(type(ax1))
# 
# ax1.set_ylim(0, 10)
# ax1.set_xlim(0, 10)
# starty, endy = ax1.get_ylim()
# print(starty)
# print(endy)
# print()
# startx, endx = ax1.get_xlim()
# print(startx)
# print(endx)
# 
# ax1.yaxis.set_ticks(np.arange(starty, endy, 1))
# ax1.xaxis.set_ticks(np.arange(startx, endx, 1))
ax1.set_ylabel('Courant (mA)')
ax1.set_xlabel('Temps (s)')
# ax1.set_ylabel('tension differentielle (mV)', color='g')
# ax1.set_xlabel('courant (mA)', color='r')
graph = FigureCanvasTkAgg(fig, master=frame9) #liaison du graph à la fenêtre tkinter créee
canvas = graph.get_tk_widget().pack(padx=20) #definir la position du graph dans la fenêtre
#canvas = graph.get_tk_widget()
#canvas.grid(row=0, column=0)

frame10 = tk.Frame(frame12) #boite permettant de center les entités : bouton, echelles etc. 
frame10.pack(pady = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame10)

labelEREF = tk.Label(frame10, text = "               E Reference (mV)   E Travail (mV)     Contre E (mV)      Courant (mA)")
labelEREF.pack()
labelEREF = tk.Label(frame10, text = "Mesures: ")
labelEREF.pack(side = tk.LEFT, padx = decallagex)
sortieEREF = tk.Entry(frame10,  state='normal', width=LongeurEntreesSorties)
sortieEREF.pack(side = tk.LEFT, padx = decallagex)
#labelET = tk.Label(frame12, text = "Tension Electrode de Travail (mV) :")
#labelET.pack()
sortieET = tk.Entry(frame10,  state='normal', width=LongeurEntreesSorties)
sortieET.pack(side = tk.LEFT, padx = decallagex)
#labelCE = tk.Label(frame12, text = "Tension Contre Electrode (mV) :")
#labelCE.pack()
sortieCE = tk.Entry(frame10,  state='normal', width=LongeurEntreesSorties)
sortieCE.pack(side = tk.LEFT, padx = decallagex)

sortieCourantTest = tk.Entry(frame10,  state='normal', width=LongeurEntreesSorties)
sortieCourantTest.pack(side = tk.LEFT, padx = decallagex)

frame13 = tk.Frame(frame12) #boite permettant de center les entités : bouton, echelles etc. 
frame13.pack() #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame13)
labelChoixEnregistrement = tk.Label(frame13, text = "Selection du numéro de l'enregistrement à afficher:")
labelChoixEnregistrement.pack(side = tk.LEFT)
#créer la liste Python contenant les éléments de la liste Combobox

listeEnregistrements=["1", "2","3","4","5","6", "7", "8", "9", "10"] # au demarrage on lit la BD et met à jour cette liste
print("listeEnregistrements: ",listeEnregistrements)
listeEnregistrements.clear()
print("listeEnregistrements: ",listeEnregistrements)
if nombreTestsBD > 0 :
    for i in range(nombreTestsBD) :
       listeEnregistrements.append(i+1)
    listeCombEnregistrements = ttk.Combobox(frame13, values=listeEnregistrements, state='normal', width=LongeurConsignes)
else :
    listeEnregistrements.append(1)
    listeCombEnregistrements = ttk.Combobox(frame13, values=listeEnregistrements, state='disabled', width=LongeurConsignes)
     
print("listeEnregistrements: ", listeEnregistrements)
#listeEnregistrements=["1", "2","3","4","5","6", "7", "8", "9", "10"] # au demarrage on lit la BD et met à jour cette liste
#Création de la Combobox via la méthode ttk.Combobox()             #  s'il n'y a pas d'enregistrement, desactiver le bouton "AFFICHER"     
# listeCombEnregistrements = ttk.Combobox(frame13, values=listeEnregistrements, state='normal', width=LongeurEntreesSorties)
# 4) - Choisir l'élément qui s'affiche par défaut
listeCombEnregistrements.current(0)
listeCombEnregistrements.pack()
listeCombEnregistrements.bind("<<ComboboxSelected>>", actionlisteEnregistrement)

frame14 = tk.Frame(frame12) #boite permettant de center les entités : bouton, echelles etc. 
frame14.pack(pady = decallagex) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame14)
labelDateDebut = tk.Label(frame14, text = "Date début:")
labelDateDebut.pack(side =tk.LEFT, padx = decallagex)
sortieDateDebut = tk.Entry(frame14,  state='normal', width=17)
sortieDateDebut.pack(side =tk.LEFT, padx = decallagex)
labelDateDebut = tk.Label(frame14, text = "Date Fin:")
labelDateDebut.pack(side= tk.LEFT, padx = decallagex)
sortieDateFin = tk.Entry(frame14,  state='normal', width=17)
sortieDateFin.pack(side = tk.LEFT, padx = decallagex)

frame15 = tk.Frame(frame12) #boite permettant de center les entités : bouton, echelles etc. 
frame15.pack(padx = decallagey) #rendre la frame visible 'expand=YES' pour s'adapter au redimentionnement de la fenetre
frames_boutons.append(frame15)
labelAfficher = tk.Label(frame15, text = "Afficher les mesures :")
labelAfficher.pack(pady = decallagex)
buttonAfficher = tk.Button(frame15, text="AFFICHER", command=ActionButtonAfficher, state=tk.DISABLED)
buttonAfficher.pack()

if (nombreTestsBD > 0) :
    buttonAfficher['state'] = tk.NORMAL
    
#FuncAnimation(fig, update_graph, interval=2000)
anifunc = FuncAnimation(fig, update_graph, interval=1000)
#ani = animation.FuncAnimation(fig, update_graph, interval=500)

fen.update() # Suivant le WM. A faire dans tous les cas donc.
fenrw = fen.winfo_reqwidth()
fenrh = fen.winfo_reqheight()
sw = fen.winfo_screenwidth()
sh = fen.winfo_screenheight()
#print(fenrw, fenrh, sw, sh)
fen.geometry("%dx%d+%d+%d" % (fenrw, fenrh, (sw-fenrw)/2, (sh-fenrh)/2))
fen.mainloop() #rendre la fenêtre visible

Pwm0.off()
Ecriture_ad5241(0x00, [0x00])
Potentiometre.off()
    