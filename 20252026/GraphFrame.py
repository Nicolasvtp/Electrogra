# Ce fichier est un fichier parent utilisé dans ElectrograApp.py
# Ce fichier permet de fournir les différentes commandes relatives aux boutons et menus déroulant créés dans ElectrograApp.py


    # ------------------------------------------------------------------------
    # --- Imports ---
    # -------------------------------------------------------------------------

from matplotlib.pyplot import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg




    # ------------------------------------------------------------------------
    # --- Initialisation de la classe ---
    # -------------------------------------------------------------------------

class GraphFrame: # Ne dépend d'aucune super classe
    def __init__(self, root):
        self.root = root
        print("Fin de l'initialisation de la sous-classe 'GraphFrame'. ")



    # ------------------------------------------------------------------------
    # --- Fonctions ---
    # -------------------------------------------------------------------------

    @staticmethod
    def creer_graphe(frame):
        print("creation graphe ok")

            # Configuration du redimensionnement du frame
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        fig = Figure(figsize=(5, 3), dpi=100, facecolor="#f0f0f0")
        #on utilise matplotlib pour faire les graphes, qu'on place dans Tk
        canvas = FigureCanvasTkAgg(fig, master=frame)   
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=0, column=0, sticky="nsew")

            #1er graphe
        ax = fig.add_subplot(111)
        ax.set_title("Valeur en fonction du temps")
        ax.set_xlabel("Temps (min)")
        ax.set_ylabel("Valeur")
        ax.grid()

        # Ajuster les marges pour éviter que les étiquettes soient coupées
        fig.tight_layout() 

    @staticmethod
    def creer_graphe_TensionVSCourant(frame):
        print("creation graphe ok")

           # Configuration du redimensionnement du frame
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        fig = Figure(figsize=(5, 3), dpi=100, facecolor="#f0f0f0")
        #on utilise matplotlib pour faire les graphes, qu'on place dans Tk
        canvas = FigureCanvasTkAgg(fig, master=frame)   
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=0, column=0, sticky="nsew")

            #2e graphe
        ax = fig.add_subplot(111)
        ax.set_title("Courbe de polarisation")
        ax.set_xlabel("Courant (A)")
        ax.set_ylabel("Tension (V)")
        ax.grid()

        # Ajuster les marges pour éviter que les étiquettes soient coupées
        fig.tight_layout() 