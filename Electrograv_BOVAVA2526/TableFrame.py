from tkinter import ttk

#crée le tableau de résultats pendant l'analyse
class TableFrame():
    def __init__(self,root):
        self.root = root
        print("table")

    @staticmethod
    def creer_table(frame):
        #Colonnes et taille
        print("creation table ok")
        tree = ttk.Treeview(frame, columns=("index", "time", "voltage", "current"), show="headings")
        tree.heading("index", text="#")
        tree.heading("time", text="Temps (min)")
        tree.heading("voltage", text="Tension (V)")
        tree.heading("current", text="Courant (mA)")
        tree.column("index", width=30, stretch=False, anchor="center")
        tree.column("time", width=80, stretch=False, anchor="center")
        tree.column("voltage", width=75, stretch=False, anchor="center")
        tree.column("current", width=85, stretch=False, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")

        #barre de scroll
        #scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        #scrollbar.pack(side="right", fill="y")             #a mettre en grid à la place de pack
        #tree.configure(yscrollcommand=scrollbar.set)