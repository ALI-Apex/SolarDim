from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import io

# ==============================
# COULEURS
# ==============================
BLEU_MARINE = colors.HexColor("#1B2A4A")
ORANGE = colors.HexColor("#F4A300")
GRIS_CLAIR = colors.HexColor("#F4F6FB")
GRIS_TEXTE = colors.HexColor("#888888")
BLANC = colors.white
VERT = colors.HexColor("#27AE60")
ROUGE = colors.HexColor("#E74C3C")


# ==============================
# STYLES
# ==============================
def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Titre",
        fontSize=22,
        textColor=BLEU_MARINE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name="SousTitre",
        fontSize=11,
        textColor=GRIS_TEXTE,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=20
    ))

    styles.add(ParagraphStyle(
        name="SectionTitre",
        fontSize=13,
        textColor=BLANC,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=0,
        spaceBefore=0,
        leftIndent=8
    ))

    styles.add(ParagraphStyle(
        name="Avertissement",
        fontSize=9,
        textColor=ROUGE,
        fontName="Helvetica-Bold",
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name="Footer",
        fontSize=8,
        textColor=GRIS_TEXTE,
        alignment=TA_CENTER
    ))

    return styles


# ==============================
# COMPOSANTS RÉUTILISABLES
# ==============================
def creer_header_section(titre: str, styles) -> list:
    elements = []
    elements.append(Spacer(1, 0.3 * cm))

    header_data = [[Paragraph(titre, styles["SectionTitre"])]]
    header_table = Table(header_data, colWidths=[17 * cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLEU_MARINE),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2 * cm))
    return elements


def creer_tableau_donnees(donnees: list) -> Table:
    table_data = [[label, valeur] for label, valeur in donnees]

    table = Table(table_data, colWidths=[8.5 * cm, 8.5 * cm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), GRIS_TEXTE),
        ("TEXTCOLOR", (1, 0), (1, -1), BLEU_MARINE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BLANC, GRIS_CLAIR]),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e0e0e0")),
    ]))
    return table


def creer_tableau_projection(projection: list) -> Table:
    entetes = ["Annee", "Economies cumulees (FCFA)", "Statut"]
    table_data = [entetes]

    for p in projection:
        statut = "Benefice" if p["economies_cumulees"] >= 0 else "En cours..."
        table_data.append([
            str(p["annee"]),
            f"{p['economies_cumulees']:,.0f}",
            statut
        ])

    table = Table(table_data, colWidths=[3 * cm, 8 * cm, 6 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLEU_MARINE),
        ("TEXTCOLOR", (0, 0), (-1, 0), BLANC),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANC, GRIS_CLAIR]),
        ("TEXTCOLOR", (0, 1), (-1, -1), BLEU_MARINE),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e0e0e0")),
    ]))
    return table


# ==============================
# GÉNÉRATION DU PDF
# ==============================
def generer_pdf_dimensionnement(
    dim: dict,
    localisation: dict,
    rentabilite: dict = None,
    moyenne: dict = None,
    parametres: dict = None
) -> bytes:

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = get_styles()
    story = []
    ville = localisation["ville"].split(",")[0] if localisation else "—"
    date_rapport = datetime.now().strftime("%d/%m/%Y a %H:%M")

    # ==============================
    # EN-TÊTE
    # ==============================
    story.append(Paragraph("SolarDim Pro", styles["Titre"]))
    story.append(Paragraph("Rapport de dimensionnement photovoltaique off-grid", styles["SousTitre"]))
    story.append(HRFlowable(width="100%", thickness=2, color=ORANGE))
    story.append(Spacer(1, 0.3 * cm))

    infos_data = [
        ["Localisation", ville],
        ["Date du rapport", date_rapport],
        ["Source consommation", "Equipements" if dim["source_consommation"] == "equipements" else "Factures"],
        ["Consommation journaliere", f"{dim['consommation_journaliere_kwh']} kWh/j"],
    ]
    story.append(creer_tableau_donnees(infos_data))

    # ==============================
    # RÉSULTATS DE BASE
    # ==============================
    story.extend(creer_header_section("RESULTATS DU DIMENSIONNEMENT", styles))

    donnees_base = [
        ["Puissance installee", f"{dim['puissance_installee_kwc']} kWc"],
        ["Nombre de panneaux", f"{dim['nombre_panneaux']} x {dim['puissance_panneau_wc']} Wc"],
        ["Capacite batterie totale", f"{dim['batterie']['capacite_ah']} Ah - {dim['batterie']['tension_v']} V"],
        ["Autonomie", f"{dim['batterie']['autonomie_jours']} jour(s)"],
        ["Onduleur recommande", f"{dim['puissance_onduleur_recommandee_kva']} kVA ({dim['puissance_onduleur_recommandee_w']} W)"],
    ]

    if rentabilite:
        donnees_base += [
            ["Retour sur investissement", f"{rentabilite['temps_retour_ans']} ans"],
            ["Economies annuelles estimees", f"{rentabilite['economies_annuelles']:,.0f} FCFA"],
        ]

    story.append(creer_tableau_donnees(donnees_base))

    # ==============================
    # DÉTAILS COMPOSANTS
    # ==============================
    lignes_composants = []

    if dim.get("configuration_strings"):
        config_strings = dim["configuration_strings"]
        for s in config_strings.get("strings", []):
            if s.get("nb_panneaux_affectes", 0) > 0:
                num = s["numero_string"]
                lignes_composants += [
                    [f"Entree PV {num} - Serie", f"{s['nb_serie_affecte']} panneaux"],
                    [f"Entree PV {num} - Parallele", f"{s['nb_parallele_affecte']} string(s)"],
                    [f"Entree PV {num} - Total affecte", f"{s['nb_panneaux_affectes']} panneaux"],
                ]
                if s.get("tension_string_v"):
                    lignes_composants.append([f"Entree PV {num} - Tension", f"{s['tension_string_v']} V"])

    if dim.get("surface_champ"):
        sf = dim["surface_champ"]
        lignes_composants += [
            ["Surface champ PV", f"{sf['surface_totale_m2']} m2 (avec aeration x1.1)"],
            ["Surface par module", f"{sf['surface_module_m2']} m2"],
        ]

    if dim.get("configuration_batterie"):
        cb = dim["configuration_batterie"]
        lignes_composants += [
            ["Configuration batterie", f"{cb['nb_batteries_serie']}S x {cb['nb_batteries_parallele']}P"],
            ["Nombre total de batteries", f"{cb['nb_batteries_total']} unites"],
            ["Tension parc batterie", f"{cb['tension_parc_v']} V"],
            ["Capacite reelle", f"{cb['capacite_reelle_ah']} Ah"],
        ]

    if lignes_composants:
        story.extend(creer_header_section("DETAILS COMPOSANTS", styles))
        story.append(creer_tableau_donnees(lignes_composants))

    # ==============================
    # AVERTISSEMENTS
    # ==============================
    avertissements = []
    if dim.get("configuration_strings"):
        for avert in dim["configuration_strings"].get("avertissements", []):
            avertissements.append(avert)
    if dim.get("configuration_batterie"):
        b = dim["configuration_batterie"]
        if b.get("avertissement_tension"):
            avertissements.append(b["avertissement_tension"])

    if avertissements:
        story.extend(creer_header_section("AVERTISSEMENTS", styles))
        for avert in avertissements:
            story.append(Paragraph(f"- {avert}", styles["Avertissement"]))
            story.append(Spacer(1, 0.2 * cm))

    # ==============================
    # FICHE TECHNIQUE
    # ==============================
    story.extend(creer_header_section("FICHE TECHNIQUE", styles))

    tarif = moyenne["tarif_moyen_fcfa_kwh"] if moyenne else (
        float(parametres["tarif_kwh"]) if parametres else 150
    )

    fiche_data = [
        ["Consommation journaliere", f"{dim['consommation_journaliere_kwh']} kWh/j"],
        ["HSP utilise", f"{dim['hsp_utilise']} h/j"],
        ["Performance Ratio", "0.65 (standard off-grid)"],
        ["Puissance crete necessaire", f"{dim['puissance_crete_necessaire_wc']} Wc"],
        ["Profondeur de decharge", f"{int(dim['batterie']['profondeur_decharge'] * 100)} %"],
        ["Tarif kWh utilise", f"{tarif} FCFA/kWh"],
    ]

    if rentabilite:
        fiche_data.append(["Cout total installation", f"{rentabilite['cout_total_installation']:,.0f} FCFA"])

    story.append(creer_tableau_donnees(fiche_data))

    # ==============================
    # PROJECTION RENTABILITÉ
    # ==============================
    if rentabilite:
        story.extend(creer_header_section("PROJECTION RENTABILITE 10 ANS", styles))
        story.append(creer_tableau_projection(rentabilite["projection_10_ans"]))

    # ==============================
    # PIED DE PAGE
    # ==============================
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=ORANGE))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Rapport genere par SolarDim Pro le {date_rapport}",
        styles["Footer"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()