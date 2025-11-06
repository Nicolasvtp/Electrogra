# Ce fichier est l'enfant de ElectrograApp.py, permettant de construire les différents menus déroulants, boutons,...
# Pour les interfaces engendrant un évènement, les paramètres 'commande_choix' ou 'commande' sont construits dans l'enfant Commandes.py

# Importation de la classe Commandes qui contient la logique des commandes
from Commandes import Commandes

# Définition de la classe InputFrame qui hérite de Commandes
class InputFrame(Commandes):
    # Constructeur de la classe
    def __init__(self, root):
        # Stockage de la fenêtre principale
        self.root = root
        print("input")
        
        # Configuration du redimensionnement de la fenêtre principale
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        #Mise en route des classes enfants
        Commandes.__init__(self,self.root)

    # Méthode pour créer le cadre principal de l'interface
    def creer_frame_parent(self):
        # Import du widget Frame de tkinter
        from tkinter import Frame

        # Création d'un cadre gris clair avec padding
        frame = Frame(self.root, bg="#f0f0f0")
        frame.grid(padx=10, pady=10, sticky="nsew")  # nsew pour étirer dans toutes les directions
        
        # Configuration du redimensionnement du frame parent
        for i in range(4):  # Pour toutes les lignes (titre, date, graphiques, tableau)
            frame.grid_rowconfigure(i, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        return frame 

    @staticmethod
    def creer_frame_enfant(frame_parent, ligne, colonne):
        from tkinter import Frame

        sous_frame = Frame(frame_parent, bg="#d0d0d0")
        sous_frame.grid(row=ligne, column=colonne, padx=10, pady=10, sticky="nsew")
        
        # Configuration du redimensionnement du sous-frame
        for i in range(6):  # Pour les 6 lignes de contrôles
            sous_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):  # Pour les 4 colonnes (boutons, labels, etc.)
            sous_frame.grid_columnconfigure(i, weight=1)
            
        return sous_frame

    @staticmethod
    def creer_label(frame, texte, ligne, colonne):
        from tkinter import Label

        label = Label(frame, text=texte, font=("Helvetica", 12), bg="#f0f0f0")
        label.grid(row=ligne, column=colonne, padx=10, pady=5, sticky="nsew")

    @staticmethod
    def creer_entry(frame, valeur, ligne, colonne, dispo):
        from tkinter import Entry

        entry = Entry(frame, textvariable=valeur, font=("Helvetica", 12), state=dispo)
        entry.grid(row=ligne, column=colonne, padx=10, pady=5, sticky="ew")  # ew pour étirer horizontalement
        return entry

    def menu_deroulant(self, frame, mode_mesure, mode_tension, entry_courant, entry_tension, menu_mode_tension, option1, option2, commande, ligne, colonne):
        from tkinter import OptionMenu
        
        # Le reste du code reste identique, mais ajoutez sticky="ew" à chaque .grid()
        match commande:
            case "courant_tension":
                menu_deroulant = OptionMenu(frame, mode_mesure, option1, option2, 
                                        command=lambda _:self.activation_inputs(mode_mesure, entry_courant, entry_tension))
                menu_deroulant.grid(row=ligne, column=colonne, padx=10, pady=5, sticky="ew")
                return menu_deroulant
            case "":
                menu_deroulant = OptionMenu(frame, mode_mesure, option1, option2)
                menu_deroulant.config(state="disabled")
                menu_deroulant.grid(row=ligne, column=colonne, padx=10, pady=5, sticky="ew")
                return menu_deroulant
            case "constant_controle":
                menu_deroulant = OptionMenu(frame, mode_tension, option1, option2, 
                                        command=lambda _:self.activation_inputs(mode_mesure, entry_courant, entry_tension, mode_tension, menu_mode_tension))
                menu_deroulant.grid(row=ligne, column=colonne, padx=10, pady=5, sticky="ew")
                return menu_deroulant
            case _:
                print("InputFrame : menu_deroulant : commande pas reconnue")

    @staticmethod
    def creer_bouton(frame, texte, commande, couleur_fond, dispo, ligne, colonne):
        from tkinter import Button

        bouton = Button(frame, text=texte, command=commande, bg=couleur_fond, fg="white", font=("Helvetica", 12), state=dispo)
        bouton.grid(row=ligne, column=colonne, padx=10, pady=5, sticky="ew")  # ew pour étirer horizontalement

    def curseur_moteur(self, frame):
        from tkinter import DoubleVar, Scale
        # Variable pour le curseur
        motor_speed_var = DoubleVar()
        
        # Curseur
        motor_speed_slider = Scale(frame, 
                                 from_=0, to=100, orient='horizontal', font=("Helvetica", 12), bg="#f0f0f0",
                                 variable=motor_speed_var, 
                                 command=lambda x: Commandes.update_motor_speed(x))
        motor_speed_slider.grid(row=1, column=0, sticky='ew')