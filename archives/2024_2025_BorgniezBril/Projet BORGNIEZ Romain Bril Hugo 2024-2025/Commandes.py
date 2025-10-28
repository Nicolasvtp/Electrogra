# Ce fichier est un enfant de InputFrame.py
# Ce fichier permet de fournir les différentes commandes relatives aux boutons et menus déroulant créés dans InputFrame.py

class Commandes():
    def __init__(self, root):
        self.root = root
        self.test_running = False
        print("commandes")

    @staticmethod
    def activation_inputs(*args):
        from tkinter import OptionMenu
        #activation_input(mode_mesure, entry_courant, entry_tension, mode_tension, menu_mode_tension)
        mode_mesure = args[0] #String
        print(f'Commandes : mode_mesure : {mode_mesure.get()}')
        entry_courant = args[1] #à (dés)activer
        print(f'Commandes : entry_courant : {entry_courant}')
        entry_tension = args[2] #à (dés)activer
        print(f'Commandes : entry_tension : {entry_tension}')
        mode_tension = args[3] if len(args) > 3 else "CONSTANT" #String, argument facultatif 
        menu_mode_tension = args[4] if len(args) > 4 else OptionMenu(None, "", "", "")
        print(f'Commandes : menu_mode_tension : {menu_mode_tension}')
        if len(args) < 4:
            menu_mode_tension.config(state="disabled")

        if mode_mesure.get() == "COURANT":
            entry_courant.config(state="normal")
            entry_tension.config(state="disabled")
            menu_mode_tension.config(state="disabled") #pas fonctionnel
            print(f'Commandes : activation_inputs : state menu_mode_tension : {menu_mode_tension.cget("state")}')
            print("Commandes : activation_input : courant ")
        else:
            entry_courant.config(state="disabled")
            entry_tension.config(state="normal")
            menu_mode_tension.config(state="normal")
            print(f'Commandes : activation_inputs : state menu_mode_tension : {menu_mode_tension.cget("state")}')
            print("Commandes : activation_input : tension ")
            if mode_tension == "CONSTANT":
                pass
            else:
                pass
    
    def start_test(self, label_test_en_cours, duree_var, mode_mesure_var, mode_tension_var, courant_var, 
                   bouton_lancer, bouton_arreter, tension_var):
        
        from tkinter import messagebox
        duree_test = duree_var.get()
        mode_mesure = mode_mesure_var.get()
        mode_tension = mode_tension_var.get()

        if duree_test and mode_tension:
            try:
                duration = int(duree_test)
                if mode_tension == "COURANT":
                    applied_current_value = courant_var.get()
                    if not applied_current_value:
                        raise ValueError("Valeur de courant non spécifiée.")
                    self.test_running = True
                    bouton_arreter.config(state="normal")
                    bouton_lancer.config(state="disabled")
                    self.afficher_test_en_cours(label_test_en_cours)
                    self.run_test(duration, None, mode_tension, applied_current_value)
                else:
                    applied_voltage_value = tension_var.get()
                    if not applied_voltage_value:
                        raise ValueError("Valeur de tension non spécifiée.")
                    if not mode_mesure:
                        raise ValueError("Mode de fonctionnement non spécifié.")
                    self.test_running = True
                    bouton_arreter.config(state="normal")
                    bouton_lancer.config(state="disabled")
                    self.afficher_test_en_cours()
                    self.run_test(duration, mode_mesure, mode_tension, applied_voltage_value)
            except ValueError as e:
                messagebox.showwarning("Avertissement", str(e))
        else:
            messagebox.showwarning("Avertissement", "Veuillez remplir tous les champs.")

    def afficher_test_en_cours(self, label_test_en_cours):
        #self.label_test_en_cours.grid()  # Affiche le label
        if self.test_running:
            current_color = label_test_en_cours.cget("fg")
            new_color = "red" if current_color == "#f0f0f0" else "#f0f0f0"
            label_test_en_cours.config(fg=new_color)
        else:
            label_test_en_cours.config(fg="#f0f0f0")
    
        self.root.after(1000, self.afficher_test_en_cours())

    def run_test(self, times, values_current, values_voltage, fig, 
                 duration, operation_mode, command_mode, applied_value):
        
        from datetime import datetime
        from matplotlib.animation import FuncAnimation

        times.clear()
        values_current.clear()
        values_voltage.clear()
        
        test_params = {
            "duration": duration,
            "operation_mode": operation_mode,
            "command_mode": command_mode,
            "applied_value": applied_value,
        }
        
        ax, bx = self.init_graph(fig, ax, bx, test_params)
        ani = FuncAnimation(fig, self.animate(ax, bx, times, values_current, values_voltage, test_params), 
                            interval=100, blit=False, save_count=duration*12)
        
        start_time = datetime.now()
        total_iterations = duration * 12
        current_iteration = 0

    def init_graph(self, fig, ax, bx, test_params):
        fig.clear()
        if test_params['command_mode'] == "COURANT":
            ax = fig.add_subplot(111)
            ax.set_title("Tension au fil du temps")
            ax.set_xlabel("Temps (min)")
            ax.set_ylabel("Tension (V)")
            scatter_ax = ax.scatter([], []) #économie de ressources, plus besoin de recréer à chaque fois un nouveau plot complet
            bx = None
        else:
            ax = fig.add_subplot(121)
            ax.set_title("Courant au fil du temps")
            ax.set_xlabel("Temps (min)")
            ax.set_ylabel("Courant (mA)")
            bx = fig.add_subplot(122)
            bx.set_title("Courant en fonction de la tension")
            bx.set_xlabel("Tension (V)")
            bx.set_ylabel("Courant (mA)")
            scatter_bx = bx.scatter([],[])
        return ax, bx


    def animate(self, fig, ax, bx, times, values_current, values_voltage, test_params):
        ax.clear()
        if bx:
            bx.clear()
        
        if test_params['command_mode'] == "COURANT":
            ax.plot(times, values_voltage, marker='o')
            ax.set_title("Tension au fil du temps")
            ax.set_xlabel("Temps (min)")
            ax.set_ylabel("Tension (V)")
            ax.grid()
        else:
            ax.plot(times, values_current, marker='o')
            ax.set_title("Courant au fil du temps")
            ax.set_xlabel("Temps (min)")
            ax.set_ylabel("Courant (mA)")
            ax.grid()
            if bx:
                bx.plot(values_voltage, values_current, marker='o')
                bx.set_title("Courant en fonction de la tension")
                bx.set_xlabel("Tension (V)")
                bx.set_ylabel("Courant (mA)")
                bx.grid()
        
        fig.tight_layout()
        return ax, bx
    
    @staticmethod
    def update_motor_speed(motor_speed_var):
        speed = float(motor_speed_var)