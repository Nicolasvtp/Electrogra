# 1. Bibliothèques standard Python
import random
import time
from datetime import datetime

# 2. Interface graphique
import tkinter as tk
from tkinter import messagebox, StringVar, OptionMenu, Entry, Button, Label, ttk, filedialog, Scale

# 3. Manipulation de données
import numpy as np
import pandas as pd
from scipy import integrate
"test"
# 4. Visualisation de données
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from matplotlib import style
import matplotlib.animation as animation
import asyncio
import io

# 5. Génération de rapports PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

# 6. Base de données
import sqlite3

# 8. Importation des classes personnalisées
from ElectrograApp import ElectrograApp
from PDF import PDF  # Assurez-vous que PDF.py est dans le même répertoire ou ajustez le chemin

'''''
# 7. Contrôle matériel et capteurs
from gpiozero import LED, PWMLED
import smbus
import ds1307 as rtc
import ADS1x15

# Get I2C bus
bus = smbus.SMBus(1)
#initialisation de l'ADS1115
ADS1115 = ADS1x15.ADS1115(1, 0x48)           # ADS1115 physiquement défini à l'adresse 0x48, avec sa broche ADDR reliée à la masse
ADS1115.setGain(ADS1115.PGA_6_144V)          # On prend le gain le plus bas (index 0), pour avoir la plus grande plage de mesure (6.144 volt)
ADS1115.setDataRate(ADS1115.DR_ADS111X_860)  # On spécifie la vitesse de mesure de tension qu'on souhaite, allant de 0 à 7 (7 étant le plus rapide, soit 860 échantillons par seconde)
ADS1115.setMode(ADS1115.MODE_SINGLE)         # On indique à l'ADC qu'on fera des mesures à la demande, et non en continu (0 = CONTINUOUS, 1 = SINGLE)
ADS1115.readADC(0)                           # Et on fait une lecture à vide, pour envoyer tous ces paramètres

#initialisation des GPIO
    #module moteur
Sens01 = LED(17)
Sens02 = LED(27)
Pwm0 = PWMLED(18)
#activation des GPIO
    #module moteur
Sens01.on()
Sens02.off()
Pwm0.value=0

#initialisation des frames, pour interface dynamique
frames_boutons = []

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
    
if not filename:  # L'utilisateur a annulé la sélection
        return

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
        '''
# Fonction pour initialiser le graphe
def init_graph():
    global ax, bx
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

def animate(frame):
    global ax, bx, times, values_current, values_voltage, test_params
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

def start_test():
    global test_running #variable booléenne pour savoir si le test est en cours
    test_duration = duration_var.get()
    operation_mode = operation_mode_var.get()
    command_mode = command_mode_var.get()

    if test_duration and command_mode:
        try:
            duration = int(test_duration)
            if command_mode == "COURANT":
                applied_current_value = current_value_var.get()
                if not applied_current_value:
                    raise ValueError("Valeur de courant non spécifiée.")
                test_running = True
                stop_button.config(state="normal")
                start_button.config(state="disabled")
                blink_text()
                run_test(duration, None, command_mode, applied_current_value)
            else:
                applied_voltage_value = voltage_value_var.get()
                if not applied_voltage_value:
                    raise ValueError("Valeur de tension non spécifiée.")
                if not operation_mode:
                    raise ValueError("Mode de fonctionnement non spécifié.")
                test_running = True
                stop_button.config(state="normal")
                start_button.config(state="disabled")
                blink_text()
                run_test(duration, operation_mode, command_mode, applied_voltage_value)
        except ValueError as e:
            messagebox.showwarning("Avertissement", str(e))
    else:
        messagebox.showwarning("Avertissement", "Veuillez remplir tous les champs.")

def run_test(duration, operation_mode, command_mode, applied_value):
    global times, values_current, values_voltage, test_params, ani
    times.clear()
    values_current.clear()
    values_voltage.clear()
    
    test_params = {
        "duration": duration,
        "operation_mode": operation_mode,
        "command_mode": command_mode,
        "applied_value": applied_value,
    }
    
    ax, bx = init_graph()
    ani = animation.FuncAnimation(fig, animate, interval=100, blit=False, save_count=duration*12)
    
    start_time = datetime.now()
    total_iterations = duration * 12
    current_iteration = 0

    def single_measurement():
        nonlocal current_iteration
        if current_iteration < total_iterations and test_running:
            current_time = datetime.now()
            elapsed_time = (current_time - start_time).total_seconds() / 60
            times.append(elapsed_time)

            measured_current = random.uniform(1, 10)
            measured_voltage = random.uniform(1, 10)
                
            values_current.append(measured_current)
            values_voltage.append(measured_voltage)

            update_table(times, values_current, values_voltage, command_mode, applied_value)
                
            current_iteration += 1
            root.after(500, single_measurement)  # Mesure réalisée toutes les 500ms
        else:
            finish_test()

    def finish_test():
        global test_running, deposited_charge
        test_running = False
        stop_button.config(state="disabled")
        start_button.config(state="normal")
        deposited_charge = integrate.trapezoid(np.array(values_current) / 1000, np.array(times)*60)
        test_params["deposited_charge"] = deposited_charge
        ani.event_source.stop()
        update_graph(ax, bx, times, values_current, values_voltage, command_mode, operation_mode, applied_value, deposited_charge)
        download_button.config(state="normal")

    single_measurement()  # Démarrer les mesures
    canvas.draw()
    
def stop_test():
       global test_running
       test_running = False
       stop_button.config(state="disabled")
       start_button.config(state="normal")
       messagebox.showinfo("Information", "Le test a été arrêté avec succès.")

def update_graph(ax, bx, times, values_current, values_voltage, command_mode, operation_mode, applied_value, deposited_charge):
    
    fig.clear()
    
    if command_mode == "COURANT":
        ax = fig.add_subplot(111)
        ax.grid()
        ax.set_title("Tension au fil du temps")
        ax.set_xlabel("Temps (min)")
        ax.set_ylabel("Tension (V)")
        label_text = f'Courant appliqué : {applied_value} mA'
        ax.text(0.03,0.98,f"Durée test : {times[-1]:.1f} min",transform=ax.transAxes, 
                fontweight='bold', verticalalignment='top')
        ax.text(0.03, 0.94, f"Charge déposée : {deposited_charge:.2f} C", 
            transform=ax.transAxes, color='red', fontweight='bold', 
            verticalalignment='top')
        ax.plot(times, values_voltage, marker='o', label=label_text)
        ax.legend(loc='lower right')

        bx = None

    elif command_mode == "TENSION" and operation_mode == "CONSTANT":
        #1er graphe
        ax = fig.add_subplot(121)
        ax.grid()
        ax.set_title("Courant au fil du temps")
        ax.set_xlabel("Temps (min)")
        ax.set_ylabel("Courant (mA)")
        label_text = f'Tension appliquée : {applied_value} V'
        ax.text(0.03,0.98,f"Durée test : {times[-1]:.1f} min",transform=ax.transAxes, 
                fontweight='bold', verticalalignment='top')
        ax.text(0.03, 0.94, f"Charge déposée : {deposited_charge:.2f} C", 
            transform=ax.transAxes, color='red', fontweight='bold', 
            verticalalignment='top')
        ax.plot(times, values_current, marker='o', label=label_text)
        ax.legend(loc='lower right')

        #2eme graphe
        bx = fig.add_subplot(122)
        bx.grid()
        bx.set_title("Courant en fonction de la tension")
        bx.set_xlabel("Tension (V)")
        bx.set_ylabel("Courant (mA)")
        label_text = f'Tension appliquée : {applied_value} V'
        bx.plot(values_voltage, values_current, marker='o', label=label_text)
        bx.legend(loc='lower right')

    else : #mode tension et mode controle
        #1er graphe
        ax = fig.add_subplot(121)
        ax.grid()
        ax.set_title("Courant au fil du temps")
        ax.set_xlabel("Temps (min)")
        ax.set_ylabel("Courant (mA)")
        label_text = f'Tension appliquée : {applied_value} V'
        ax.text(0.03,0.98,f"Durée test : {times[-1]:.1f} min",transform=ax.transAxes, 
                fontweight='bold', verticalalignment='top')
        ax.text(0.03, 0.94, f"Charge déposée : {deposited_charge:.2f} C", 
            transform=ax.transAxes, color='red', fontweight='bold', 
            verticalalignment='top')
        ax.plot(times, values_current, marker='o', label=label_text)
        ax.legend(loc='lower right')

        #2eme graphe
        bx = fig.add_subplot(122)
        bx.grid()
        bx.set_title("Courant en fonction de la tension")
        bx.set_xlabel("Tension (V)")
        bx.set_ylabel("Courant (mA)")
        label_text = f'Tension appliquée : {applied_value} V'
        bx.plot(values_voltage, values_current, marker='o', label=label_text)
        bx.legend(loc='lower right')

    canvas.draw()

def update_table(times, values_current, values_voltage, command_mode, applied_value):
    for i in tree.get_children():
        tree.delete(i)
    
    # Ajout des données
    for i, (time, voltage, current) in enumerate(zip(times, values_voltage, values_current)):
        tree.insert("", "end", values=(i+1, f"{time:.2f}", f"{voltage:.2f}", f"{current:.2f}"))

    # Mise à jour du titre du tableau
    #if command_mode == "COURANT":
    #    tree_title = f"Mesures - Courant appliqué: {applied_value} mA"
    #else:
    #    tree_title = f"Mesures - Tension appliquée: {applied_value} V"
    
    #print(tree_title)

def update_time():
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    date_label.config(text=f"Date: {current_time}")
    root.after(1000, update_time)

def on_command_mode_change(*args):
    if command_mode_var.get() == "COURANT":
        operation_mode_menu.config(state="disabled")
        current_value_entry.config(state="normal")
        voltage_value_entry.config(state="disabled")
    else:
        operation_mode_menu.config(state="normal")
        current_value_entry.config(state="disabled")
        voltage_value_entry.config(state="normal")

def generate_pdf():
    plt.ioff()
    filename = filedialog.asksaveasfilename(
        initialfile=datetime.now().strftime("%Y%m%d_%H%M%S") + "_test_results.pdf",
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    
    if not filename:  # L'utilisateur a annulé la sélection
        messagebox.showinfo("Information", "Génération du PDF annulée.")
        return

    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("Résultats du test électrogravimétrique", styles['Title']))
    elements.append(Spacer(1, 12))

    # Paramètres du test
    elements.append(Paragraph("Paramètres du test:", styles['Heading2']))
    params = [
        ["Durée du test", f"{test_params['duration']} minutes"],
        ["Mode de commande", test_params['command_mode']],
    ]
    if test_params['command_mode'] != "COURANT":
        params.append(["Mode de fonctionnement", test_params['operation_mode']])
    params.append([f"{'Courant' if test_params['command_mode'] == 'COURANT' else 'Tension'} appliqué(e)", 
                   f"{test_params['applied_value']} {'mA' if test_params['command_mode'] == 'COURANT' else 'V'}"])
    params.append(["Charge déposée", f"{test_params['deposited_charge']:.2f} C"])
    
    t = Table(params)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                           ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                           ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                           ('FONTSIZE', (0, 0), (-1, 0), 14),
                           ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                           ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                           ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                           ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                           ('FONTSIZE', (0, 0), (-1, -1), 12),
                           ('TOPPADDING', (0, 0), (-1, -1), 6),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                           ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # Graphiques
    elements.append(Paragraph("Graphiques des résultats:", styles['Heading2']))
    
    if test_params['command_mode'] == "COURANT":
        # Un seul graphe pour le mode COURANT
        plt.figure(figsize=(7, 5))
        plt.plot(times, values_voltage, marker='o')
        plt.title("Tension vs Temps")
        plt.xlabel("Temps (min)")
        plt.ylabel("Tension (V)")
        plt.grid(True)
        plt.legend([f"Courant appliqué: {test_params['applied_value']} mA"])
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        img = Image(img_buffer, width=15*cm, height=10*cm)
        elements.append(img)
        
    else:  # Mode TENSION
        # Premier graphe : Courant vs Temps
        plt.figure(figsize=(7, 5))
        plt.plot(times, values_current, marker='o')
        plt.title("Courant vs Temps")
        plt.xlabel("Temps (min)")
        plt.ylabel("Courant (mA)")
        plt.grid(True)
        plt.legend([f"Tension appliquée: {test_params['applied_value']} V"])
        
        img_buffer1 = io.BytesIO()
        plt.savefig(img_buffer1, format='png', dpi=300, bbox_inches='tight')
        img_buffer1.seek(0)
        img1 = Image(img_buffer1, width=15*cm, height=10*cm)
        elements.append(img1)
        elements.append(Spacer(1, 12))
        
        # Deuxième graphe : Courant vs Tension
        plt.figure(figsize=(7, 5))
        plt.plot(values_voltage, values_current, marker='o')
        plt.title("Courant vs Tension")
        plt.xlabel("Tension (V)")
        plt.ylabel("Courant (mA)")
        plt.grid(True)
        plt.legend([f"Tension appliquée: {test_params['applied_value']} V"])
        
        img_buffer2 = io.BytesIO()
        plt.savefig(img_buffer2, format='png', dpi=300, bbox_inches='tight')
        img_buffer2.seek(0)
        img2 = Image(img_buffer2, width=15*cm, height=10*cm)
        elements.append(img2)
    elements.append(Paragraph("Tableau des données:", styles['Heading2']))
    data = [["#", "Temps (min)", "Tension (V)", "Courant (mA)"]]
    for i, (time, voltage, current) in enumerate(zip(times, values_voltage, values_current)):
        data.append([i+1, f"{time:.2f}", f"{voltage:.2f}", f"{current:.2f}"])
    t = Table(data)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                           ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                           ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                           ('FONTSIZE', (0, 0), (-1, 0), 12),
                           ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                           ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                           ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                           ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                           ('FONTSIZE', (0, 0), (-1, -1), 10),
                           ('TOPPADDING', (0, 0), (-1, -1), 6),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                           ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    elements.append(t)

    doc.build(elements)
    messagebox.showinfo("Succès", f"Le fichier PDF a été sauvegardé avec succès à l'emplacement:\n{filename}")

def update_motor_speed(motor_speed_var):
    speed = float(motor_speed_var)

def blink_text():
    if test_running:
        current_color = test_running_label.cget("fg")
        new_color = "red" if current_color == "#f0f0f0" else "#f0f0f0"
        test_running_label.config(fg=new_color)
    else:
        test_running_label.config(fg="#f0f0f0")
    
    root.after(1000, blink_text)

    #########################################################
    #                  Interface graphique
    #########################################################
    # Fenêtre principale
root = tk.Tk()
root.title("Tests Electrogravitométriques")
root.geometry("1280x720")
root.configure(bg="#f0f0f0")

    #Cadre supérieur
header_frame = tk.Frame(root, bg="#f0f0f0")
header_frame.pack(pady=10)
        #Titre
title_label = Label(header_frame, text="Tests Electrogravitométriques", font=("Helvetica", 16), bg="#f0f0f0")
title_label.pack()
        #Date mise à jour toutes les secondes
date_label = Label(header_frame, font=("Helvetica", 10), bg="#f0f0f0")
date_label.pack()
update_time()

    #Nouveau cadre, entrées commandes
input_frame = tk.Frame(root, bg="#f0f0f0")
input_frame.pack(pady=10)
        #Durée du test
duration_var = StringVar()
duration_label = Label(input_frame, text="Durée du test (min) :", font=("Helvetica", 12), bg="#f0f0f0")
duration_label.grid(row=0, column=0, padx=10, pady=5)
duration_entry = Entry(input_frame, textvariable=duration_var, font=("Helvetica", 12))
duration_entry.grid(row=0, column=1, padx=10, pady=5)
        #Mode de commande
command_mode_var = StringVar(value="COURANT")
command_mode_label = Label(input_frame, text="Mode de commande :", font=("Helvetica", 12), bg="#f0f0f0")
command_mode_label.grid(row=1, column=0, padx=10, pady=5)
command_mode_menu = OptionMenu(input_frame, command_mode_var, "TENSION", "COURANT", command=on_command_mode_change)
command_mode_menu.grid(row=1, column=1, padx=10, pady=5)
        #Mode de fonctionnement
operation_mode_var = StringVar(value="CONTROLE")
operation_mode_label = Label(input_frame, text="Mode de fonctionnement :", font=("Helvetica", 12), bg="#f0f0f0")
operation_mode_label.grid(row=1, column=2, padx=10, pady=5)
operation_mode_menu = OptionMenu(input_frame, operation_mode_var, "CONSTANT", "CONTROLE")
operation_mode_menu.grid(row=1, column=3, padx=10, pady=5)
        #Valeur du courant
current_value_var = StringVar()
current_value_label = Label(input_frame, text="Valeur du courant (mA) :", font=("Helvetica", 12), bg="#f0f0f0")
current_value_label.grid(row=2, column=0, padx=10, pady=5)
current_value_entry = Entry(input_frame, textvariable=current_value_var, font=("Helvetica", 12), state="normal")
current_value_entry.grid(row=2, column=1, padx=10, pady=5)
        #Valeur de la tension
voltage_value_var = StringVar()
voltage_value_label = Label(input_frame, text="Valeur de la tension (V) :", font=("Helvetica", 12), bg="#f0f0f0")
voltage_value_label.grid(row=2, column=2, padx=10, pady=5)
voltage_value_entry = Entry(input_frame, textvariable=voltage_value_var, font=("Helvetica", 12), state="disabled")
voltage_value_entry.grid(row=2, column=3, padx=10, pady=5)

        #Bouton lancer le test
start_button = Button(input_frame, text="Lancer le test", command=start_test, bg="#4CAF50", fg="white", font=("Helvetica", 12))
#start_button.pack(side="left", padx=10)
start_button.grid(row=3, column=0, padx=10, pady=5)
        #Bouton télécharger PDF
download_button = Button(input_frame, text="Télécharger PDF", command=generate_pdf, bg="#800000", fg="white", font=("Helvetica", 12), state="disabled")
#download_button.pack(side="left", padx=10)
download_button.grid(row=1, column=4, padx=10, pady=5)
        #Bouton arrêt du test
stop_button = Button(input_frame, text="Arrêter le test", command=stop_test, bg="#FF0000", fg="white", font=("Helvetica", 12), state='disabled')
stop_button.grid(row=3, column=1, padx=10, pady=5)
test_running = False
        #Curseur vitesse moteur
motor_frame = tk.Frame(input_frame, bg="#f0f0f0")
motor_frame.grid(row=0, column=2, columnspan=2, padx=10, sticky='ew')
motor_speed_label = tk.Label(motor_frame, text='Vitesse du moteur (%)', font=("Helvetica", 12), bg="#f0f0f0")
motor_speed_label.pack(pady=(0, 0.5))
motor_speed_var = tk.DoubleVar()
motor_speed_slider = Scale(motor_frame, from_=0, to=100, orient='horizontal', font=("Helvetica", 12), bg="#f0f0f0",
                           variable=motor_speed_var, command=update_motor_speed)
motor_speed_slider.pack(fill='x')
        #Texte test en cours
test_running_label = Label(input_frame, text="Test en cours...", font=("Helvetica", 12), bg="#f0f0f0", fg="#f0f0f0")
test_running_label.grid(row=3, column=2, padx=10, pady=5)

    #Cadre graphe
content_frame = tk.Frame(root, bg="#f0f0f0")
content_frame.pack(side="left", fill="both", expand=True, pady=10)

fig = plt.Figure(figsize=(5, 3), dpi=100, facecolor="#f0f0f0")

    #1er graphe
#ax = fig.add_subplot(121)
#ax.set_title("Tension vs Courant")
#ax.set_xlabel("Temps (min)")
#ax.set_ylabel("Valeur")
#ax.grid()

    #2nd graphe
#bx = fig.add_subplot(122)
#bx.set_title("Courant en fonction de la tension")
#bx.set_xlabel("Tension (V)")
#bx.set_ylabel("Courant (mA)")
#bx.grid()
        #on utilise matplotlib pour faire les graphes, qu'on place dans Tk
canvas = FigureCanvasTkAgg(fig, master=content_frame)   
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side="left", fill="both", expand=True)

    #Cadre tableau résultats
table_frame = tk.Frame(content_frame, bg="#f0f0f0")
table_frame.pack(side="right", fill="both", expand=False, padx=10)
        #Colonnes et taille
tree = ttk.Treeview(table_frame, columns=("index", "time", "voltage", "current"), show="headings")
tree.heading("index", text="#")
tree.heading("time", text="Temps (min)")
tree.heading("voltage", text="Tension (V)")
tree.heading("current", text="Courant (mA)")
tree.column("index", width=30, stretch=False, anchor="center")
tree.column("time", width=80, stretch=False, anchor="center")
tree.column("voltage", width=75, stretch=False, anchor="center")
tree.column("current", width=85, stretch=False, anchor="center")
tree.pack(fill="both", expand=True)
        #barre de scroll
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
scrollbar.pack(side="right", fill="y")
tree.configure(yscrollcommand=scrollbar.set)



##############################
#     Boucle principale
##############################
#from tkinter import Tk
#from ElectrograApp import electrograApp

if __name__ == "__main__": #permet de lancer le programme sans run les imports au début (économie de ressources)
    #root = Tk()
    #app = electrograApp(root)
    on_command_mode_change()
    times, values_current, values_voltage, test_params = [], [], [], {}
    root.mainloop() #Boucle événementielle Tkinter

