import tkinter as tk
from tkinter import messagebox, StringVar, OptionMenu, Entry, Button, Label, ttk, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import random
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io
import os

def start_test():
    test_duration = duration_var.get()
    operation_mode = operation_mode_var.get()
    command_mode = command_mode_var.get()

    if test_duration and command_mode:
        try:
            duration = int(test_duration)
            if command_mode == "COURANT":
                current_value = current_value_var.get()
                if not current_value:
                    raise ValueError("Valeur de courant non spécifiée.")
                run_test(duration, None, command_mode, current_value)
            else:
                voltage_value = voltage_value_var.get()
                if not voltage_value:
                    raise ValueError("Valeur de tension non spécifiée.")
                if not operation_mode:
                    raise ValueError("Mode de fonctionnement non spécifié.")
                run_test(duration, operation_mode, command_mode, voltage_value)
        except ValueError as e:
            messagebox.showwarning("Avertissement", str(e))
    else:
        messagebox.showwarning("Avertissement", "Veuillez remplir tous les champs.")

def run_test(duration, operation_mode, command_mode, value):
    global times, values, test_params
    times = []
    values = []
    
    start_time = datetime.now()
    for i in range(duration * 12):
        current_time = datetime.now()
        elapsed_time = (current_time - start_time).total_seconds()
        times.append(elapsed_time)

        if command_mode == "COURANT":
            measured_value = random.uniform(1, 10)
        else:
            measured_value = random.uniform(1, 10)
        values.append(measured_value)
        
        time.sleep(0.1)  # Réduit pour la démonstration, normalement 5 secondes

    test_params = {
        "duration": duration,
        "operation_mode": operation_mode,
        "command_mode": command_mode,
        "applied_value": value
    }

    update_graph(times, values, command_mode, value)
    update_table(times, values, command_mode, value)
    download_button.config(state="normal")

def update_graph(times, values, command_mode, applied_value):
    ax.clear()
    ax.set_title(f"{command_mode} vs Temps")
    ax.set_xlabel("Temps (min)")
    ax.set_ylabel(f"{'Tension (V)' if command_mode == 'COURANT' else 'Courant (mA)'}")
    ax.grid()
    
    if command_mode == "COURANT":
        label_text = f'Courant appliqué: {applied_value} mA'
    else:
        label_text = f'Tension appliquée: {applied_value} V'

    ax.plot(times, values, marker='o', label=label_text)
    ax.legend()
    canvas.draw()

def update_table(times, values, command_mode, applied_value):
    for i in tree.get_children():
        tree.delete(i)
    
    for i, (time, value) in enumerate(zip(times, values)):
        tree.insert("", "end", values=(i+1, f"{time:.2f}", f"{value:.2f}"))
    
    if command_mode == "COURANT":
        tree.heading("value", text=f"Tension (V) - Courant appliqué: {applied_value} mA")
    else:
        tree.heading("value", text=f"Courant (mA) - Tension appliquée: {applied_value} V")

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
    filename = filedialog.asksaveasfilename(
        initialfile=datetime.now().strftime("%Y%m%d_%H%M%S") + "_test_results.pdf",
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    
    if not filename:  # L'utilisateur a annulé la sélection
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

    # Graphique
    plt.figure(figsize=(7, 5))
    plt.plot(times, values, marker='o')
    plt.title(f"{test_params['command_mode']} vs Temps")
    plt.xlabel("Temps (min)")
    plt.ylabel(f"{'Tension (V)' if test_params['command_mode'] == 'COURANT' else 'Courant (mA)'}")
    plt.grid(True)
    if test_params['command_mode'] == "COURANT":
        plt.legend([f"Courant appliqué: {test_params['applied_value']} mA"])
    else:
        plt.legend([f"Tension appliquée: {test_params['applied_value']} V"])
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    img = Image(img_buffer, width=6*inch, height=4*inch)
    elements.append(Paragraph("Graphique des résultats:", styles['Heading2']))
    elements.append(img)
    elements.append(Spacer(1, 12))

    # Tableau de données
    elements.append(Paragraph("Tableau des données:", styles['Heading2']))
    data = [["#", "Temps (s)", f"{'Tension (V)' if test_params['command_mode'] == 'COURANT' else 'Courant (mA)'}"]]
    for i, (time, value) in enumerate(zip(times, values)):
        data.append([i+1, f"{time:.2f}", f"{value:.2f}"])
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

root = tk.Tk()
root.title("Tests Electrogravitométriques")
root.geometry("1080x760")
root.configure(bg="#f0f0f0")

header_frame = tk.Frame(root, bg="#f0f0f0")
header_frame.pack(pady=10)

title_label = Label(header_frame, text="Tests Electrogravitométriques", font=("Helvetica", 16), bg="#f0f0f0")
title_label.pack()

date_label = Label(header_frame, font=("Helvetica", 10), bg="#f0f0f0")
date_label.pack()
update_time()

input_frame = tk.Frame(root, bg="#f0f0f0")
input_frame.pack(pady=10)

duration_var = StringVar()
duration_label = Label(input_frame, text="Durée du test (min) :", font=("Helvetica", 12), bg="#f0f0f0")
duration_label.grid(row=0, column=0, padx=10, pady=5)
duration_entry = Entry(input_frame, textvariable=duration_var, font=("Helvetica", 12))
duration_entry.grid(row=0, column=1, padx=10, pady=5)

command_mode_var = StringVar(value="COURANT")
command_mode_label = Label(input_frame, text="Mode de commande :", font=("Helvetica", 12), bg="#f0f0f0")
command_mode_label.grid(row=1, column=0, padx=10, pady=5)
command_mode_menu = OptionMenu(input_frame, command_mode_var, "TENSION", "COURANT", command=on_command_mode_change)
command_mode_menu.grid(row=1, column=1, padx=10, pady=5)

operation_mode_var = StringVar(value="CONTROLE")
operation_mode_label = Label(input_frame, text="Mode de fonctionnement :", font=("Helvetica", 12), bg="#f0f0f0")
operation_mode_label.grid(row=2, column=0, padx=10, pady=5)
operation_mode_menu = OptionMenu(input_frame, operation_mode_var, "CONSTANT", "CONTROLE")
operation_mode_menu.grid(row=2, column=1, padx=10, pady=5)

current_value_var = StringVar()
current_value_label = Label(input_frame, text="Valeur du courant (mA) :", font=("Helvetica", 12), bg="#f0f0f0")
current_value_label.grid(row=3, column=0, padx=10, pady=5)
current_value_entry = Entry(input_frame, textvariable=current_value_var, font=("Helvetica", 12), state="normal")
current_value_entry.grid(row=3, column=1, padx=10, pady=5)

voltage_value_var = StringVar()
voltage_value_label = Label(input_frame, text="Valeur de la tension (V) :", font=("Helvetica", 12), bg="#f0f0f0")
voltage_value_label.grid(row=4, column=0, padx=10, pady=5)
voltage_value_entry = Entry(input_frame, textvariable=voltage_value_var, font=("Helvetica", 12), state="disabled")
voltage_value_entry.grid(row=4, column=1, padx=10, pady=5)

button_frame = tk.Frame(root, bg="#f0f0f0")
button_frame.pack(pady=10)

start_button = Button(button_frame, text="Lancer le test", command=start_test, bg="#4CAF50", fg="white", font=("Helvetica", 12))
start_button.pack(side="left", padx=10)

download_button = Button(button_frame, text="Télécharger PDF", command=generate_pdf, bg="#008CBA", fg="white", font=("Helvetica", 12), state="disabled")
download_button.pack(side="left", padx=10)

content_frame = tk.Frame(root, bg="#f0f0f0")
content_frame.pack(fill="both", expand=True, pady=10)

fig = plt.Figure(figsize=(5, 3), dpi=100)
ax = fig.add_subplot(111)
ax.set_title("Tension vs Courant")
ax.set_xlabel("Temps (min)")
ax.set_ylabel("Valeur")
ax.grid()

canvas = FigureCanvasTkAgg(fig, master=content_frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side="left", fill="both", expand=True)

table_frame = tk.Frame(content_frame, bg="#f0f0f0")
table_frame.pack(side="right", fill="both", expand=True, padx=10)

tree = ttk.Treeview(table_frame, columns=("index", "time", "value"), show="headings")
tree.heading("index", text="#")
tree.heading("time", text="Temps (min)")
tree.heading("value", text="Valeur")
tree.column("index", width=50)
tree.column("time", width=100)
tree.column("value", width=100)
tree.pack(fill="both", expand=True)

scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
scrollbar.pack(side="right", fill="y")
tree.configure(yscrollcommand=scrollbar.set)

on_command_mode_change()

times, values, test_params = [], [], {}

root.mainloop()


# rajouter les Coulomb tel que Q = i * t