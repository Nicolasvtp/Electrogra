import matplotlib.pyplot as plt
from tkinter import filedialog, messagebox
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import io
import pandas as pd

class PDF:
    @staticmethod
    def generate_pdf(test_params, times, values_voltage, values_current):
        plt.ioff()  # Désactive le mode interactif de matplotlib
        
        # Création du nom de fichier avec la date et l'heure
        default_filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_test_results"
        
        # Demande à l'utilisateur où sauvegarder le PDF
        pdf_filename = filedialog.asksaveasfilename(
            initialfile=default_filename + ".pdf",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if not pdf_filename:
            messagebox.showinfo("Information", "Génération du PDF annulée.")
            return

        # Création du fichier Excel avec les données
        excel_filename = pdf_filename.replace('.pdf', '.xlsx')
        df = pd.DataFrame({
            'Temps (min)': times,
            'Tension (V)': values_voltage,
            'Courant (mA)': values_current
        })
        df.to_excel(excel_filename, index=False, sheet_name='Données')
        
        # Création du document PDF
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        elements = []
        styles = getSampleStyleSheet()

        # Titre et date
        elements.append(Paragraph("Résultats du test électrogravimétrique", styles['Title']))
        elements.append(Paragraph(f"Date du test: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 
                                styles['Normal']))
        elements.append(Spacer(1, 12))

        # Paramètres du test
        elements.append(Paragraph("Paramètres du test:", styles['Heading2']))
        params = [["Paramètre", "Valeur"]]  # En-tête du tableau
        
        # Ajout dynamique des paramètres
        for key, value in test_params.items():
            if key == 'duration':
                params.append(["Durée du test", f"{value} minutes"])
            elif key == 'command_mode':
                params.append(["Mode de commande", value])
            elif key == 'operation_mode' and test_params.get('command_mode') != "COURANT":
                params.append(["Mode de fonctionnement", value])
            elif key == 'applied_value':
                unit = 'mA' if test_params.get('command_mode') == 'COURANT' else 'V'
                params.append([f"{'Courant' if unit == 'mA' else 'Tension'} appliqué(e)", f"{value} {unit}"])
            elif key == 'deposited_charge':
                params.append(["Charge déposée", f"{value:.2f} C"])

        # Style du tableau des paramètres
        param_table = Table(params)
        param_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(param_table)
        elements.append(Spacer(1, 20))

        # Génération des graphiques
        elements.append(Paragraph("Graphiques des résultats:", styles['Heading2']))
        
        # Fonction helper pour créer un graphique
        def create_plot(x_data, y_data, title, xlabel, ylabel, legend_text):
            plt.figure(figsize=(8, 6))
            plt.plot(x_data, y_data, marker='o', linestyle='-', linewidth=2, markersize=4)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.grid(True)
            if legend_text:
                plt.legend([legend_text])
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            return Image(buffer, width=15*cm, height=10*cm)

        # Graphique Tension vs Temps
        elements.append(create_plot(
            times, values_voltage,
            "Tension en fonction du Temps",
            "Temps (min)", "Tension (V)",
            f"Mode: {test_params.get('command_mode', 'N/A')}"
        ))
        elements.append(Spacer(1, 12))

        # Graphique Courant vs Temps
        elements.append(create_plot(
            times, values_current,
            "Courant en fonction du Temps",
            "Temps (min)", "Courant (mA)",
            None
        ))
        elements.append(Spacer(1, 12))

        # Graphique Tension vs Courant
        elements.append(create_plot(
            values_current, values_voltage,
            "Tension en fonction du Courant",
            "Courant (mA)", "Tension (V)",
            None
        ))

        # Tableau des données
        elements.append(Paragraph("Données brutes:", styles['Heading2']))
        data = [["N°", "Temps (min)", "Tension (V)", "Courant (mA)"]]
        for i, (time, voltage, current) in enumerate(zip(times, values_voltage, values_current), 1):
            data.append([i, f"{time:.2f}", f"{voltage:.2f}", f"{current:.2f}"])

        # Style du tableau des données
        data_table = Table(data)
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(data_table)

        # Note sur le fichier Excel
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            f"Note: Un fichier Excel contenant les données brutes a été créé: {excel_filename}",
            styles['Italic']
        ))

        # Génération du PDF
        doc.build(elements)
        messagebox.showinfo("Succès", 
            f"Les fichiers ont été sauvegardés avec succès:\n"
            f"PDF: {pdf_filename}\n"
            f"Excel: {excel_filename}"
        )
