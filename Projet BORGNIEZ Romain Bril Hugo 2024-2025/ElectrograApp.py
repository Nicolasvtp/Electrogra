""" Cette classe est une sous-classe ayant comme héritant des classes InputFrame, GraphFrame et TableFrame

Elle assemble les cadres d’entrée (InputFrame),
les graphiques (GraphFrame) et le tableau de données (TableFrame), et expose
les actions utilisateur (lancer/arrêter le test, générer un PDF).

"""

# ------------------------------------------------------------------------
# --- Imports ---
# -------------------------------------------------------------------------
from InputFrame import InputFrame          # Importe la classe gérant les widgets d’entrée
from GraphFrame import GraphFrame          # Importe la classe gérant les graphiques
from TableFrame import TableFrame          # Importe la classe gérant le tableau de données
from tkinter import Label                  # Importe le widget Label depuis Tkinter (affichage de texte)
from PDF import PDF                        # Importe le module d’export PDF
from tkinter import Tk                     # Importe le constructeur de la fenêtre principale Tk
from tkinter import StringVar                          # Variables Tk liées aux widgets (Entry/OptionMenu)



# ------------------------------------------------------------------------
# --- Initialisation de la classe  ---
# -------------------------------------------------------------------------
class ElectrograApp(InputFrame, GraphFrame, TableFrame): # Hérite de InputFrame, GraphFrame et TableFrame
    def __init__(self):

        # --- Fenêtre principale ----
        # Création de la fenêtre racine Tkinter (le conteneur principal de l’UI).
        self.root = Tk()                                        # l’objet fenêtre principale TK dans une variable de classe, référence la fenêtre dans la classe
        self.root.title("Tests Electrogravitométriques")        # Définit le titre affiché dans la barre de la fenêtre
        self.root.geometry("1280x720")                          # Fixe une taille initiale (largeur x hauteur en pixels)
        self.root.configure(bg="#f0f0f0")                       # Définit la couleur de fond de la fenêtre

        # Configure la grille principale pour qu’elle se redimensionne
        # (weight=1 permet d’étirer la ligne/colonne quand la fenêtre change de taille).
        self.root.grid_rowconfigure(0, weight=1)                # La ligne 0 de la grille principale peut grandir
        self.root.grid_columnconfigure(0, weight=1)             # La colonne 0 de la grille principale peut grandir

        # --- Modèle de données -------------------------------------------------
        # Listes qui stockeront les séries temporelles pendant le test.
        self.times = []                                         # Horodatages (x-axes)
        self.values_voltage = []                                # Mesures de tension (y1)
        self.values_current = []                                # Mesures de courant (y2)

        # Dictionnaire de paramètres courants de la session de test.
        self.test_params = {
            'duration': 0,               # Durée du test en minutes (valeur entrée par l’utilisateur)
            'command_mode': 'COURANT',   # Mode de consigne : "COURANT" ou "TENSION"
            'operation_mode': 'CONSTANT',# Mode de fonctionnement : "CONSTANT" ou "CONTROLE" (PID)
            'applied_value': 0,          # Valeur de consigne (mA si COURANT, V si TENSION)
            'deposited_charge': 0        # Charge déposée (unité selon convention aval)
        }

        print("Fin de l'initialisation de la sous-classe 'ElectrograApp'. ")

        # --- Initialisation des super-classes  -------------------------------------
        # Chaque mixin reçoit la root (fenetre principale) pour créer ses propres widgets dans l’arbre Tkinter.
        # C'est à ce moment ci que les super-classes desquells dépend ElectrograApp dépend
        InputFrame.__init__(self, self.root)                   # Initialise les utilitaires/éléments d’entrée -- Obligatoire lorsque la classe hérite.
        GraphFrame.__init__(self, self.root)                   # Initialise les graphes (figure/canvas, etc.)
        TableFrame.__init__(self, self.root)                   # Initialise le tableau (Treeview, colonnes, etc.)

        # --- Construction de l’interface --------------------------------------
        self.creer_interface_graphique()                       # Construit toute la mise en page/les widgets visibles
        print("tâche finie (init electro) ")                   # Log console (debug)



# ------------------------------------------------------------------------
# --- Fonctions ---
# -------------------------------------------------------------------------

    def generer_pdf(self):
        """
        Exporte les résultats courants du test au format PDF
        en déléguant à PDF.generate_pdf(...).
        """
        PDF.generate_pdf(                                      # Appel de la fonction d’export
            self.test_params,                                  # Paramètres de test (métadonnées)
            self.times,                                        # Série temps
            self.values_voltage,                               # Série tension
            self.values_current                                # Série courant
        )


    def creer_interface_graphique(self):
        # -- Bandeau titre/date -------------------------------------------------
        # Cadre parent supérieur (contiendra le titre et la date).
        self.frame_titre = super().creer_frame_parent()        # Méthode fournie par InputFrame pour créer un frame de haut niveau
        super().creer_label(self.frame_titre,                  # Crée un Label “titre” dans frame_titre
                            "Tests Electrogravitométriques",
                            0, 0)
        super().creer_label(self.frame_titre,                  # Crée un Label “Date mise à jour” (statique pour l’instant)
                            "Date mise à jour",
                            1, 0)  # TODO: connecter à une horloge via root.after(...)

        # -- Cadre des entrées (paramétrage) -----------------------------------
        # Cadre enfant pour regrouper toutes les entrées de configuration.
        self.frame_input = super().creer_frame_enfant(self.frame_titre, 2, 0)  # Placé ligne 2, colonne 0 sous le titre

        # Durée du test (en minutes)
        super().creer_label(self.frame_input,                  # Label pour l’entrée “durée”
                            "Durée du test (min) : ",
                            0, 0)
        duree_var = StringVar()                                # Variable Tk liée à l’Entry (texte ↔ code)
        entry_duree = super().creer_entry(self.frame_input,    # Champ d’entrée pour la durée (état normal)
                                          duree_var,
                                          0, 1,
                                          "normal")

        # Valeur du courant (mA)
        super().creer_label(self.frame_input,                  # Label pour l’entrée “courant”
                            "Valeur du courant (mA) :",
                            3, 0)
        courant_var = StringVar()                              # Variable Tk pour le courant
        entry_courant = super().creer_entry(self.frame_input,  # Entry désactivée par défaut (activée via menu)
                                            courant_var,
                                            3, 1,
                                            "disabled")

        # Valeur de la tension (V)
        super().creer_label(self.frame_input,                  # Label pour l’entrée “tension”
                            "Valeur de la tension (V) :",
                            4, 0)
        tension_var = StringVar()                              # Variable Tk pour la tension
        entry_tension = super().creer_entry(self.frame_input,  # Entry désactivée par défaut (activée via menu)
                                            tension_var,
                                            4, 1,
                                            "disabled")

        # Mode de mesure : COURANT/TENSION (sélection via menu déroulant)
        super().creer_label(self.frame_input,                  # Label du menu “Mode de mesure”
                            "Mode de mesure :",
                            1, 0)
        mode_mesure_var = StringVar(value="COURANT")           # Valeur initiale = "COURANT"
        super().menu_deroulant(                                # Crée le menu et gère l’activation des entrées associées
            self.frame_input,
            mode_mesure_var,     # Variable de choix (COURANT/TENSION)
            None,                # Pas de variable “mode_tension” à lier ici
            entry_courant,       # Widget à activer si “COURANT”
            entry_tension,       # Widget à activer si “TENSION”
            None,                # Pas de second menu à synchroniser ici
            "COURANT", "TENSION",
            "courant_tension",   # Clé d’aiguillage côté Commandes.py
            1, 1                 # Position dans la grille
        )

        # Mode de fonctionnement : CONSTANT/CONTROLE (PID)
        super().creer_label(self.frame_input,                  # Label du menu “Mode de fonctionnement”
                            "Mode de fonctionnement :",
                            2, 0)
        mode_tension_var = StringVar(value="CONSTANT")         # Valeur initiale = "CONSTANT"

        # Premier appel : crée un menu “structurel” et récupère son widget (pour chaînage).
        menu_mode_tension = super().menu_deroulant(
            self.frame_input, None, None, None, None, None,
            "CONSTANT", "CONTROLE", "",                        # Les options du menu (texte)
            2, 1
        )

        # Deuxième appel : relie dynamiquement le choix de mesure (COURANT/TENSION)
        # et le mode (CONSTANT/CONTROLE) aux entrées activées/désactivées.
        super().menu_deroulant(
            self.frame_input,
            mode_mesure_var,     # Dépend du choix précédent
            mode_tension_var,    # Variable pour ce menu-ci
            entry_courant,       # Entrée courant potentiellement activée
            entry_tension,       # Entrée tension potentiellement activée
            menu_mode_tension,   # Menu à mettre à jour si besoin
            "CONSTANT", "CONTROLE",
            "constant_controle", # Clé d’aiguillage côté Commandes.py
            2, 1
        )

        # -- Zone de contrôle du test ------------------------------------------
        # Label “TEST EN COURS …” (feedback visuel), masqué par défaut.
        self.label_test_en_cours = Label(self.frame_input,     # Création du Label avec parent = frame_input
                                         text="TEST EN COURS ...",
                                         bg="#f0f0f0")
        self.label_test_en_cours.grid(row=5, column=1)         # Placement sur la grille (mais on va le cacher)
        self.label_test_en_cours.grid_remove()                  # Masque le widget (il garde sa place logique)

        # Bouton : Lancer le test
        # La callback appelle start_test(...) (doit exister côté Commandes/InputFrame).
        bouton_lancer = super().creer_bouton(
            self.frame_input,
            "Lancer le test",
            lambda: self.start_test(                            # Callback exécutée au clic
                self.label_test_en_cours,                      # Pour pouvoir l’afficher/masquer pendant le test
                duree_var,                                     # Durée (StringVar)
                mode_mesure_var,                               # Mode mesure (StringVar)
                mode_tension_var,                              # Mode fonctionnement (StringVar)
                courant_var,                                   # Consigne courant (StringVar)
                bouton_lancer,                                 # Pour éventuellement désactiver le bouton
                bouton_arreter,                                # Pour activer/désactiver l’arrêt (capturé par closure)
                tension_var                                    # Consigne tension (StringVar)
            ),
            "#4CAF50", "normal", 5, 0                          # Couleur, état, position
        )

        # Bouton : Arrêter le test (ici, il ne fait que masquer le label ; la logique d’arrêt réel est à implémenter ailleurs).
        bouton_arreter = super().creer_bouton(
            self.frame_input,
            "Arrêter le test",
            lambda: self.cacher_test_en_cours(),               # Callback : cache le label
            "#FF0000", "normal", 5, 2
        )

        # Bouton : Générer le PDF (export des données actuelles).
        super().creer_bouton(
            self.frame_input,
            "Télécharger le PDF",
            lambda: self.generer_pdf(),                        # Callback : appelle PDF.generate_pdf(...)
            "#800000", "normal", 5, 3
        )

        # -- Graphiques ---------------------------------------------------------
        # Frame pour le(s) graphe(s) temporel(s) (tension/courant vs temps).
        self.frame_graphes = super().creer_frame_enfant(self.frame_titre, 3, 0)  # Position sous le titre
        super().creer_graphe(self.frame_graphes)               # Crée et/ou monte le canvas matplotlib dans ce frame

        # Frame pour le graphe Tension vs Courant (caractéristique V–I).
        self.frame_graphe_tension_courant = super().creer_frame_enfant(self.frame_titre, 3, 1)
        super().creer_graphe_TensionVSCourant(self.frame_graphe_tension_courant)

        # -- Tableau de données -------------------------------------------------
        # Frame contenant la table (ex. ttk.Treeview) avec les colonnes temps/V/I.
        self.frame_table = super().creer_frame_enfant(self.frame_titre, 2, 1)
        super().creer_table(self.frame_table)

        # -- Curseur moteur -----------------------------------------------------
        # Frame pour le contrôle de la vitesse moteur (ex. Scale 0–100%).
        self.frame_curseur_moteur = super().creer_frame_enfant(self.frame_titre, 2, 2)
        super().creer_label(self.frame_curseur_moteur, 'Vitesse du moteur (%)', 0, 0)
        super().curseur_moteur(self.frame_curseur_moteur)      # Ajoute le widget de curseur (Scale) et sa logique

        # ✅ À améliorer (si besoin) :
        # - Lier “Date mise à jour” à une horloge (root.after(1000, ...)) pour l’actualiser chaque seconde.
        # - Valider/convertir les StringVar en float/int avant start_test (gestion d’erreurs utilisateur).

    # -------------------------------------------------------------------------
    # Feedback visuel “test en cours”
    # -------------------------------------------------------------------------
    def afficher_test_en_cours(self):
        """Affiche le label indiquant qu’un test est en cours."""
        self.label_test_en_cours.grid()                        # Ré-affiche le label (inverse de .grid_remove())

    def cacher_test_en_cours(self):
        """Masque le label indiquant qu’un test est en cours."""
        self.label_test_en_cours.grid_remove()                 # Cache le label (sans détruire le widget)


# ----- BOUCLE PRINCIPALE (temporaire ici, à déplacer dans main.py) -----------
if __name__ == "__main__":                                     # Point d’entrée si on exécute ce fichier directement
    app = ElectrograApp()                                      # Instancie l’app (crée root et construit l’UI)
    print("ca tourne")
    app.root.mainloop()                                        # Lance la boucle évènementielle Tk (bloque jusqu’à fermeture)
    print("Fin de la simulation")                              # Log après fermeture de la fenêtre
