import logging
from datetime import datetime
import streamlit as st
import plotly.graph_objects as go
from core.storage import get_localisation, get_consommation_moyenne, get_parametres
from core.sizing import calculer_rentabilite
from export.pdf_generator import generer_pdf_dimensionnement

logger = logging.getLogger(__name__)

PERFORMANCE_RATIO = 0.65


def afficher_metriques_dimensionnement() -> None:
    if "dim" not in st.session_state:
        return

    dim = st.session_state.dim
    localisation = get_localisation()
    moyenne = get_consommation_moyenne()
    parametres = get_parametres()
    ville = localisation["ville"].split(",")[0] if localisation else "site"

    tarif = moyenne["tarif_moyen_fcfa_kwh"] if moyenne else float(parametres["tarif_kwh"])
    prix_installation = float(parametres["prix_total_installation"])

    rentabilite = None
    if prix_installation > 0 and localisation:
        try:
            rentabilite = calculer_rentabilite(
                prix_total_installation=prix_installation,
                production_annuelle_kwh=float(localisation["irradiation_annuelle_kwh"]) * dim["puissance_installee_kwc"],
                tarif_kwh=tarif,
            )
            st.session_state.rentabilite = rentabilite
        except (ValueError, KeyError) as e:
            logger.error("Erreur calcul rentabilité : %s", e)

    st.markdown("---")
    col_resultats, col_graphe = st.columns(2)

    # ----------------------------
    # COLONNE GAUCHE : RÉSULTATS
    # ----------------------------
    with col_resultats:
        st.subheader("⚡ Résultats du dimensionnement")

        lignes_base = ""
        lignes_base += f"<tr><td>Puissance installée</td><td><strong>{dim['puissance_installee_kwc']} kWc</strong></td></tr>"
        lignes_base += f"<tr><td>Nombre de panneaux</td><td><strong>{dim['nombre_panneaux']} × {dim['puissance_panneau_wc']} Wc</strong></td></tr>"
        lignes_base += f"<tr><td>Capacité batterie</td><td><strong>{dim['batterie']['capacite_ah']} Ah — {dim['batterie']['tension_v']} V</strong></td></tr>"
        lignes_base += f"<tr><td>Autonomie</td><td><strong>{dim['batterie']['autonomie_jours']} jour(s)</strong></td></tr>"
        lignes_base += f"<tr><td>Onduleur recommandé</td><td><strong>{dim['puissance_onduleur_recommandee_kva']} kVA</strong></td></tr>"

        if rentabilite:
            lignes_base += f"<tr><td>Retour sur investissement</td><td><strong>{rentabilite['temps_retour_ans']} ans</strong></td></tr>"
            lignes_base += f"<tr><td>Économies annuelles</td><td><strong>{rentabilite['economies_annuelles']:,.0f} FCFA</strong></td></tr>"

        table_base = "<table class='result-table'>"
        table_base += "<thead><tr><th colspan='2'>⚡ BASE</th></tr></thead>"
        table_base += "<tbody>" + lignes_base + "</tbody>"
        table_base += "</table>"
        st.markdown(table_base, unsafe_allow_html=True)

        # --- Tableau enrichi ---
        lignes_enrichies = ""

        if dim.get("configuration_strings"):
            for s in dim["configuration_strings"].get("strings", []):
                if s.get("nb_panneaux_affectes", 0) > 0:
                    n = s["numero_string"]
                    lignes_enrichies += f"<tr><td>Entrée PV {n} — Série</td><td><strong>{s['nb_serie_affecte']} panneaux</strong></td></tr>"
                    lignes_enrichies += f"<tr><td>Entrée PV {n} — Parallèle</td><td><strong>{s['nb_parallele_affecte']} string(s)</strong></td></tr>"
                    lignes_enrichies += f"<tr><td>Entrée PV {n} — Total affecté</td><td><strong>{s['nb_panneaux_affectes']} panneaux</strong></td></tr>"
                    if s.get("nb_serie_min") and s.get("nb_serie_max_mppt"):
                        lignes_enrichies += f"<tr><td>Entrée PV {n} — Plage série</td><td><strong>{s['nb_serie_min']} à {s['nb_serie_max_mppt']}</strong></td></tr>"
                    if s.get("tension_string_v"):
                        lignes_enrichies += f"<tr><td>Entrée PV {n} — Tension</td><td><strong>{s['tension_string_v']} V</strong></td></tr>"

        if dim.get("surface_champ"):
            sf = dim["surface_champ"]
            lignes_enrichies += f"<tr><td>Surface champ PV</td><td><strong>{sf['surface_totale_m2']} m²</strong></td></tr>"
            lignes_enrichies += f"<tr><td>Surface par module</td><td><strong>{sf['surface_module_m2']} m²</strong></td></tr>"

        if dim.get("configuration_batterie"):
            cb = dim["configuration_batterie"]
            lignes_enrichies += f"<tr><td>Configuration batterie</td><td><strong>{cb['nb_batteries_serie']}S × {cb['nb_batteries_parallele']}P</strong></td></tr>"
            lignes_enrichies += f"<tr><td>Nombre total batteries</td><td><strong>{cb['nb_batteries_total']} unités</strong></td></tr>"
            lignes_enrichies += f"<tr><td>Tension parc batterie</td><td><strong>{cb['tension_parc_v']} V</strong></td></tr>"
            lignes_enrichies += f"<tr><td>Capacité réelle</td><td><strong>{cb['capacite_reelle_ah']} Ah</strong></td></tr>"

        if lignes_enrichies:
            table_enrichi = "<table class='result-table' style='margin-top: 16px;'>"
            table_enrichi += "<thead><tr><th colspan='2'>🔧 DÉTAILS COMPOSANTS</th></tr></thead>"
            table_enrichi += "<tbody>" + lignes_enrichies + "</tbody>"
            table_enrichi += "</table>"
            st.markdown(table_enrichi, unsafe_allow_html=True)

        # --- Avertissements ---
        avertissements = []
        if dim.get("configuration_strings"):
            avertissements.extend(dim["configuration_strings"].get("avertissements", []))
            non_affectes = dim["configuration_strings"].get("panneaux_non_affectes", 0)
            if non_affectes > 0:
                avertissements.append(f"⚠️ {non_affectes} panneau(x) non affecté(s)")

        if dim.get("configuration_batterie") and dim["configuration_batterie"].get("avertissement_tension"):
            avertissements.append(dim["configuration_batterie"]["avertissement_tension"])

        if avertissements:
            st.markdown("<br>", unsafe_allow_html=True)
            for avert in avertissements:
                st.warning(avert)

    # ----------------------------
    # COLONNE DROITE : GRAPHE + FICHE TECHNIQUE
    # ----------------------------
    with col_graphe:
        if rentabilite:
            st.subheader("💰 Projection rentabilité 10 ans")
            afficher_graphe_rentabilite(rentabilite)
        else:
            st.info("💡 Renseignez le prix total de l'installation dans **Configurations → Paramètres économiques**.")

        st.markdown("---")
        st.subheader("📄 Fiche technique")

        lignes_fiche = ""
        lignes_fiche += f"<tr><td>Consommation journalière</td><td><strong>{dim['consommation_journaliere_kwh']} kWh/j</strong></td></tr>"
        lignes_fiche += f"<tr><td>Source consommation</td><td><strong>{'Équipements' if dim['source_consommation'] == 'equipements' else 'Factures'}</strong></td></tr>"
        lignes_fiche += f"<tr><td>HSP utilisé</td><td><strong>{dim['hsp_utilise']} h/j</strong></td></tr>"
        lignes_fiche += f"<tr><td>Performance Ratio</td><td><strong>{PERFORMANCE_RATIO}</strong></td></tr>"
        lignes_fiche += f"<tr><td>Puissance crête nécessaire</td><td><strong>{dim['puissance_crete_necessaire_wc']} Wc</strong></td></tr>"
        lignes_fiche += f"<tr><td>Profondeur de décharge</td><td><strong>{int(dim['batterie']['profondeur_decharge'] * 100)} %</strong></td></tr>"
        if rentabilite:
            lignes_fiche += f"<tr><td>Coût installation</td><td><strong>{rentabilite['cout_total_installation']:,.0f} FCFA</strong></td></tr>"

        table_fiche = "<table class='result-table'>"
        table_fiche += "<thead><tr><th colspan='2'>📄 FICHE TECHNIQUE</th></tr></thead>"
        table_fiche += "<tbody>" + lignes_fiche + "</tbody>"
        table_fiche += "</table>"
        st.markdown(table_fiche, unsafe_allow_html=True)

    # --- Export PDF ---
    st.markdown("<br>", unsafe_allow_html=True)
    try:
        pdf_bytes = generer_pdf_dimensionnement(
            dim=dim,
            localisation=localisation,
            rentabilite=rentabilite,
            moyenne=moyenne,
            parametres=parametres
        )
        st.download_button(
            label="📥 Exporter en PDF",
            data=pdf_bytes,
            file_name=f"dimensionnement_{ville}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    except Exception as e:
        logger.error("Erreur génération PDF : %s", e)
        st.error("❌ Erreur lors de la génération du PDF.")


def afficher_graphe_rentabilite(rentabilite: dict) -> None:
    annees = [0] + [p["annee"] for p in rentabilite["projection_10_ans"]]
    valeurs = [-rentabilite["cout_total_installation"]] + [
        p["economies_cumulees"] for p in rentabilite["projection_10_ans"]
    ]
    couleurs = ["#E74C3C" if v < 0 else "#27AE60" for v in valeurs]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=annees,
        y=valeurs,
        mode="lines+markers",
        line=dict(color="#1B2A4A", width=2),
        marker=dict(size=6, color=couleurs),
        fill="tozeroy",
        fillcolor="rgba(244, 163, 0, 0.1)"
    ))
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#E74C3C",
        annotation_text="Seuil de rentabilité",
        annotation_position="bottom right",
        annotation_font_color="#1B2A4A"
    )
    fig.update_layout(
        xaxis_title="Années",
        yaxis_title="Gain cumulé (FCFA)",
        xaxis=dict(title_font=dict(color="#1B2A4A", size=13), tickfont=dict(color="#1B2A4A"), gridcolor="#e0e0e0"),
        yaxis=dict(title_font=dict(color="#1B2A4A", size=13), tickfont=dict(color="#1B2A4A"), gridcolor="#e0e0e0"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#1B2A4A"),
        height=280,
        margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)


def afficher_rapport_agent() -> None:
    if "dim" not in st.session_state:
        st.info("💡 Lancez d'abord une analyse depuis l'accueil.")
        return
    st.info("🚧 Fonctionnalité en cours de développement — disponible prochainement.")