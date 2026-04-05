import html
import logging
from datetime import datetime
import streamlit as st
import plotly.graph_objects as go
from core.storage import get_localisation, get_consommation_moyenne, get_parametres
from core.sizing import calculer_rentabilite
from export.pdf_generator import generer_pdf_dimensionnement

from config import PERFORMANCE_RATIO_DEFAULT

logger = logging.getLogger(__name__)


def afficher_metriques_dimensionnement() -> None:
    if "dim" not in st.session_state:
        return

    dim = st.session_state.dim
    localisation = get_localisation()
    moyenne = get_consommation_moyenne()
    parametres = get_parametres()
    ville = localisation["ville"].split(",")[0] if localisation else "site"

    tarif = moyenne["tarif_moyen_fcfa_kwh"] if (moyenne and moyenne.get("tarif_moyen_fcfa_kwh")) else float(parametres["tarif_kwh"])
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
        except (ValueError, KeyError, TypeError) as e:
            logger.error("Erreur calcul rentabilité : %s", e)

    st.markdown("---")

    # ---- Zone 1 : KPI Cards ----
    roi_class = "gray"
    roi_value = "—"
    roi_sub = "Prix installation non renseigné"
    if rentabilite:
        roi_ans = rentabilite["temps_retour_ans"]
        roi_value = f"{roi_ans} ans"
        roi_sub = f"Économies : {rentabilite['economies_annuelles']:,.0f} FCFA/an"
        roi_class = "green" if roi_ans <= 10 else "dark"

    st.markdown(f"""
    <div class='kpi-row'>
        <div class='kpi-card dark'>
            <div class='kpi-label'>Puissance installée</div>
            <div class='kpi-value'>{dim['puissance_installee_kwc']} kWc</div>
            <div class='kpi-sub'>{dim['nombre_panneaux']} × {dim['puissance_panneau_wc']} Wc</div>
        </div>
        <div class='kpi-card light'>
            <div class='kpi-label'>Batterie</div>
            <div class='kpi-value'>{dim['batterie']['capacite_ah']} Ah</div>
            <div class='kpi-sub'>{dim['batterie']['tension_v']} V — {dim['batterie']['autonomie_jours']} jour(s)</div>
        </div>
        <div class='kpi-card light'>
            <div class='kpi-label'>Onduleur recommandé</div>
            <div class='kpi-value'>{dim['puissance_onduleur_recommandee_kva']} kVA</div>
            <div class='kpi-sub'>Off-grid</div>
        </div>
        <div class='kpi-card {roi_class}'>
            <div class='kpi-label'>Retour investissement</div>
            <div class='kpi-value'>{roi_value}</div>
            <div class='kpi-sub'>{roi_sub}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Zone 2 : Component Cards ----
    strings_html = ""
    if dim.get("configuration_strings"):
        for s in dim["configuration_strings"].get("strings", []):
            if s.get("nb_panneaux_affectes", 0) > 0:
                strings_html += f"<div class='cc-row'><span>Entrée PV {s['numero_string']}</span><span>{s['nb_serie_affecte']}S × {s['nb_parallele_affecte']}P</span></div>"

    surface_html = ""
    if dim.get("surface_champ"):
        surface_html = f"<div class='cc-row'><span>Surface champ</span><span>{dim['surface_champ']['surface_totale_m2']} m²</span></div>"

    batterie_html = f"""
        <div class='cc-row'><span>Configuration</span><span>—</span></div>
        <div class='cc-row'><span>Nb batteries</span><span>—</span></div>
        <div class='cc-row'><span>Tension parc</span><span>{dim['batterie']['tension_v']} V</span></div>
        <div class='cc-row'><span>Capacité réelle</span><span>{dim['batterie']['capacite_ah']} Ah</span></div>
    """
    if dim.get("configuration_batterie"):
        cb = dim["configuration_batterie"]
        batterie_html = f"""
            <div class='cc-row'><span>Configuration</span><span>{cb['nb_batteries_serie']}S × {cb['nb_batteries_parallele']}P</span></div>
            <div class='cc-row'><span>Nb batteries</span><span>{cb['nb_batteries_total']} unités</span></div>
            <div class='cc-row'><span>Tension parc</span><span>{cb['tension_parc_v']} V</span></div>
            <div class='cc-row'><span>Capacité réelle</span><span>{cb['capacite_reelle_ah']} Ah</span></div>
        """

    source = "Équipements" if dim["source_consommation"] == "equipements" else "Factures"

    st.markdown(f"""
    <div class='component-cards-row'>
        <div class='component-card'>
            <div class='cc-title'>🔆 Panneaux PV</div>
            <div class='cc-row'><span>Nb panneaux</span><span>{dim['nombre_panneaux']}</span></div>
            <div class='cc-row'><span>Puissance unitaire</span><span>{dim['puissance_panneau_wc']} Wc</span></div>
            {strings_html}
            {surface_html}
        </div>
        <div class='component-card'>
            <div class='cc-title'>🔋 Parc Batterie</div>
            {batterie_html}
        </div>
        <div class='component-card'>
            <div class='cc-title'>📄 Fiche technique</div>
            <div class='cc-row'><span>Consommation</span><span>{dim['consommation_journaliere_kwh']} kWh/j</span></div>
            <div class='cc-row'><span>Source</span><span>{source}</span></div>
            <div class='cc-row'><span>HSP utilisé</span><span>{dim['hsp_utilise']} h/j</span></div>
            <div class='cc-row'><span>Performance Ratio</span><span>{PERFORMANCE_RATIO_DEFAULT}</span></div>
            <div class='cc-row'><span>DoD batterie</span><span>{int(dim['batterie']['profondeur_decharge'] * 100)} %</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Avertissements ----
    avertissements = []
    if dim.get("configuration_strings"):
        avertissements.extend(dim["configuration_strings"].get("avertissements", []))
        non_affectes = dim["configuration_strings"].get("panneaux_non_affectes", 0)
        if non_affectes > 0:
            avertissements.append(f"⚠️ {non_affectes} panneau(x) non affecté(s)")
    if dim.get("configuration_batterie") and dim["configuration_batterie"].get("avertissement_tension"):
        avertissements.append(dim["configuration_batterie"]["avertissement_tension"])
    for avert in avertissements:
        st.warning(avert)

    # ---- Zone 3 : Graphe + Export ----
    if rentabilite:
        st.subheader("💰 Projection rentabilité 10 ans")
        afficher_graphe_rentabilite(rentabilite)
    else:
        st.info("💡 Renseignez le prix total de l'installation dans **Configurations → Paramètres économiques** pour voir la rentabilité.")

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
            file_name=f"raana_{ville}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
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