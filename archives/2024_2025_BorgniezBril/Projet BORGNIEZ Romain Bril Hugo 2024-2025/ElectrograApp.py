# Ce fichier est le premier enfant de main.py
# Ce fichier permet de mettre en forme l'application electrogra en construisant des interfaces graphiques. 
# Les différents interfaces graphiques sont construits sur base de InputFrame.py (menu déroulant, bouton,...), GraphFrame.py et TableFrame.py

from InputFrame import InputFrame
from GraphFrame import GraphFrame
from TableFrame import TableFrame
from tkinter import Label
from PDF import PDF
import tkinter as tk

class ElectrograApp(InputFrame, GraphFrame, TableFrame):  
    def __init__(self):
        from tkinter import Tk
        #Initiation de l'instance fenêtre de l'application
        self.root = Tk()
        self.root.title("Tests Electrogravitométriques")
        self.root.geometry("1280x720")
        self.root.configure(bg="#f0f0f0")

        # Configuration du redimensionnement de la fenêtre principale
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Variables pour stocker les données du test
        self.times = []
        self.values_voltage = []
        self.values_current = []
        self.test_params = {
            'duration': 0,
            'command_mode': 'COURANT',
            'operation_mode': 'CONSTANT',
            'applied_value': 0,
            'deposited_charge': 0
        }

        #Mise en route des classes enfants
        InputFrame.__init__(self,self.root)
        GraphFrame.__init__(self,self.root)
        TableFrame.__init__(self,self.root)

        self.creer_interface_graphique()
        print("tâche finie (init electro) ")

    def generer_pdf(self):
        # Appel de la méthode generate_pdf de la classe PDF
        PDF.generate_pdf(
            self.test_params,
            self.times,
            self.values_voltage,
            self.values_current
        )

    def creer_interface_graphique(self):
        from tkinter import StringVar

        #Creation du frame contenant le titre et la date mise à jour
        self.frame_titre = super().creer_frame_parent()
        super().creer_label(self.frame_titre, "Tests Electrogravitométriques", 0, 0)
        super().creer_label(self.frame_titre, "Date mise à jour", 1, 0)

        #Nouveau cadre, entrées commandes
        self.frame_input = super().creer_frame_enfant(self.frame_titre,2,0)
        
        # Ajout du curseur moteur
        #self.curseur_moteur(self.frame_input)
        
        #Durée du test
        super().creer_label(self.frame_input, "Durée du test (min) : ", 0, 0)
        duree_var = StringVar()
        entry_duree = super().creer_entry(self.frame_input, duree_var, 0, 1, "normal")

        #Valeur du courant
        super().creer_label(self.frame_input, "Valeur du courant (mA) :", 3, 0)
        courant_var = StringVar()
        entry_courant = super().creer_entry(self.frame_input, courant_var, 3, 1, "disabled")
        
        #Valeur de la tension
        super().creer_label(self.frame_input, "Valeur de la tension (V) :", 4, 0)
        tension_var = StringVar()
        entry_tension = super().creer_entry(self.frame_input, tension_var, 4, 1, "disabled")

        #Mode de mesure
        super().creer_label(self.frame_input, "Mode de mesure :", 1, 0)
        mode_mesure_var = StringVar(value="COURANT") #par défaut
        super().menu_deroulant(self.frame_input, mode_mesure_var, None, entry_courant, entry_tension, None, 
                              "COURANT", "TENSION", "courant_tension", 1, 1)

        #Mode de tension
        super().creer_label(self.frame_input, "Mode de fonctionnement :", 2, 0)
        mode_tension_var = StringVar(value="CONSTANT") #par défaut
        menu_mode_tension = super().menu_deroulant(self.frame_input, None, None, None, None, None, 
                                                 "CONSTANT", "CONTROLE", "", 2, 1)
        super().menu_deroulant(self.frame_input, mode_mesure_var, mode_tension_var, entry_courant, entry_tension, menu_mode_tension,  
                              "CONSTANT", "CONTROLE", "constant_controle", 2, 1)

        #Démarrer le test
        # Création directe du label avec tkinter
        self.label_test_en_cours = Label(self.frame_input, text="TEST EN COURS ...", bg="#f0f0f0")
        self.label_test_en_cours.grid(row=5, column=1)
        self.label_test_en_cours.grid_remove()  # Cache initialement le label
        
        bouton_lancer = super().creer_bouton(self.frame_input, "Lancer le test", 
                                            lambda: self.start_test(self.label_test_en_cours, duree_var, mode_mesure_var, mode_tension_var, courant_var, 
                                                                    bouton_lancer, bouton_arreter, tension_var), 
                                            "#4CAF50", "normal", 5, 0)
        
        #Arreter le test
        bouton_arreter = super().creer_bouton(self.frame_input, "Arrêter le test", 
                                             lambda: self.cacher_test_en_cours(), 
                                             "#FF0000", "normal", 5, 2)
        
        #Générer le PDF
        super().creer_bouton(self.frame_input, "Télécharger le PDF", 
                            lambda: self.generer_pdf(), 
                            "#800000", "normal", 5, 3)

        #Cadre graphe
        self.frame_graphes = super().creer_frame_enfant(self.frame_titre,3,0)
        super().creer_graphe(self.frame_graphes)

        #Nouveau cadre pour le graphe Tension vs Courant
        self.frame_graphe_tension_courant = super().creer_frame_enfant(self.frame_titre,3,1)
        super().creer_graphe_TensionVSCourant(self.frame_graphe_tension_courant)

        #Cadre table
        self.frame_table = super().creer_frame_enfant(self.frame_titre,2,1)
        super().creer_table(self.frame_table)

        #Cadre curseur moteur
        self.frame_curseur_moteur = super().creer_frame_enfant(self.frame_titre,2,2)
        super().creer_label(self.frame_curseur_moteur, 'Vitesse du moteur (%)', 0, 0)
        super().curseur_moteur(self.frame_curseur_moteur)

    def afficher_test_en_cours(self):
        self.label_test_en_cours.grid()  # Affiche le label
    
    def cacher_test_en_cours(self):
        self.label_test_en_cours.grid_remove()  # Cache le label


#-----BOUCLE PRINCIPALE-------      à mettre dans main.py
if __name__ == "__main__":
    app = ElectrograApp()
    print("ca tourne")
    app.root.mainloop()
    print("Fin de la simulation")