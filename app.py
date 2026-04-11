import streamlit as st
from dotenv import load_dotenv
from ui.style import get_css
from core.storage import initialiser_stockage

load_dotenv(override=True)  # Charge .env en priorité sur les variables système

st.set_page_config(
    page_title="Raana",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown(get_css(), unsafe_allow_html=True)
initialiser_stockage()

if "page_active" not in st.session_state:
    st.session_state.page_active = "Factures"

# ==============================
# WIZARD CONFIG
# ==============================
WIZARD_STEPS = [
    ("📄", "Factures"),
    ("🔌", "Équipements"),
    ("📍", "Localisation"),
    ("🔧", "Configurations"),
    ("⚡", "Analyse"),
]
WIZARD_STEP_NAMES = [nom for _, nom in WIZARD_STEPS]
SIDEBAR_PAGES = ["Guide & Notions", "Analyse IA"]


def _get_step_status(step_nom: str, data: dict) -> str:
    """Retourne 'done', 'active' ou 'pending' pour une étape du wizard."""
    if step_nom == st.session_state.page_active:
        return "active"
    if step_nom == "Factures" and data.get("factures"):
        return "done"
    if step_nom == "Équipements" and data.get("equipements"):
        return "done"
    if step_nom == "Localisation" and data.get("localisation"):
        return "done"
    if step_nom == "Configurations" and any([data.get("module"), data.get("onduleur"), data.get("batterie")]):
        return "done"
    if step_nom == "Analyse" and "dim" in st.session_state:
        return "done"
    return "pending"


def _afficher_wizard_bar(data: dict) -> None:
    """Affiche la barre de progression wizard en HTML."""
    html = "<div class='wizard-bar'>"
    for i, (icone, nom) in enumerate(WIZARD_STEPS):
        statut = _get_step_status(nom, data)
        label_circle = "✓" if statut == "done" else str(i + 1)
        html += f"""
        <div class='wizard-step'>
            <div class='wizard-step-circle {statut}'>{label_circle}</div>
            <div class='wizard-step-label {statut}'>{icone} {nom}</div>
        </div>"""
        if i < len(WIZARD_STEPS) - 1:
            connector_class = "done" if statut == "done" else "pending"
            html += f"<div class='wizard-connector {connector_class}'></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ==============================
# SIDEBAR SIMPLIFIÉE
# ==============================
with st.sidebar:
    st.markdown("""
        <div style='text-align:center; padding: 20px 0 16px 0;'>
            <div style='font-size:44px;'>☀️</div>
            <div style='font-size:26px; font-weight:bold; color:white; letter-spacing:2px;'>Raana</div>
            <div style='font-size:12px; color:#aaa;'>Fahishal</div>
        </div>
        <div style='height:1px; background:#1a2a4a; margin:0 8px 12px 8px;'></div>
    """, unsafe_allow_html=True)

    for icone, nom in zip(["📖", "🤖"], SIDEBAR_PAGES):
        is_active = st.session_state.page_active == nom
        btn_style = "background:#F4A300 !important; color:white !important; font-weight:bold !important;"
        if is_active:
            st.markdown(f"<style>[data-testid='stSidebar'] [data-testid='stBaseButton-secondary']:has(p:contains('{nom}')) {{ {btn_style} }}</style>", unsafe_allow_html=True)
        if st.button(f"{icone}  {nom}", key=f"nav_{nom}", use_container_width=True):
            st.session_state.page_active = nom
            st.rerun()

    st.markdown("<div style='height:1px; background:#1a2a4a; margin:12px 8px 0 8px;'></div>", unsafe_allow_html=True)

    # Boutons étapes wizard dans la sidebar (accès rapide)
    st.markdown("<div style='font-size:10px; color:#555; padding: 8px 16px; text-transform:uppercase; letter-spacing:0.5px;'>Étapes</div>", unsafe_allow_html=True)
    for icone, nom in WIZARD_STEPS:
        if st.button(f"{icone} {nom}", key=f"nav_wizard_{nom}", use_container_width=True):
            st.session_state.page_active = nom
            st.rerun()

# ==============================
# DONNÉES POUR WIZARD BAR
# ==============================
page = st.session_state.page_active

from core.storage import (
    get_factures, get_equipements, get_localisation,
    get_consommation_moyenne, get_module_pv,
    get_onduleur, get_batterie, get_strings
)
from core.sizing import calculer_dimensionnement_complet

factures = get_factures()
equipements = get_equipements()
localisation = get_localisation()
module = get_module_pv()
onduleur_data = get_onduleur()
batterie_u = get_batterie()
strings = get_strings()
moyenne = get_consommation_moyenne()

_wizard_data = {
    "factures": factures,
    "equipements": equipements,
    "localisation": localisation,
    "module": module,
    "onduleur": onduleur_data,
    "batterie": batterie_u,
}

# ==============================
# PAGES SIDEBAR (hors wizard)
# ==============================
if page == "Guide & Notions":
    st.markdown("<div class='page-title'>📖 Guide & Notions</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Comprendre les concepts et utiliser l'outil efficacement</div>", unsafe_allow_html=True)
    from ui.guide import afficher_guide
    afficher_guide()

elif page == "Analyse IA":
    st.markdown("<div class='page-title'>🤖 Analyse IA</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Posez une question à l'agent solaire</div>", unsafe_allow_html=True)
    from ui.results_display import afficher_rapport_agent
    afficher_rapport_agent()

# ==============================
# PAGES WIZARD
# ==============================
else:
    # S'assurer que la page est valide
    if page not in WIZARD_STEP_NAMES:
        st.session_state.page_active = "Factures"
        st.rerun()

    _afficher_wizard_bar(_wizard_data)
    step_index = WIZARD_STEP_NAMES.index(page)

    # ----------------------------
    # ÉTAPE 1 — FACTURES
    # ----------------------------
    if page == "Factures":
        st.markdown("<div class='page-title'>📄 Factures d'électricité</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-subtitle'>Uploadez vos factures pour estimer votre consommation</div>", unsafe_allow_html=True)
        from ui.input_forms import afficher_formulaire_factures
        afficher_formulaire_factures()

    # ----------------------------
    # ÉTAPE 2 — ÉQUIPEMENTS
    # ----------------------------
    elif page == "Équipements":
        st.markdown("<div class='page-title'>🔌 Équipements électriques</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-subtitle'>Listez vos appareils pour estimer votre consommation</div>", unsafe_allow_html=True)
        from ui.input_forms import afficher_formulaire_equipements
        afficher_formulaire_equipements()

    # ----------------------------
    # ÉTAPE 3 — LOCALISATION
    # ----------------------------
    elif page == "Localisation":
        st.markdown("<div class='page-title'>📍 Localisation du site</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-subtitle'>Données d'ensoleillement via PVGIS</div>", unsafe_allow_html=True)
        from ui.localisation_composants import afficher_localisation
        afficher_localisation()

    # ----------------------------
    # ÉTAPE 4 — CONFIGURATIONS
    # ----------------------------
    elif page == "Configurations":
        st.markdown("<div class='page-title'>🔧 Configurations</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-subtitle'>Renseignez vos composants et les paramètres économiques</div>", unsafe_allow_html=True)
        from ui.localisation_composants import afficher_composants
        afficher_composants()

    # ----------------------------
    # ÉTAPE 5 — ANALYSE
    # ----------------------------
    elif page == "Analyse":
        st.markdown("<div class='page-title'>⚡ Analyse & Résultats</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-subtitle'>Dimensionnement complet de votre installation</div>", unsafe_allow_html=True)
        from ui.results_display import afficher_metriques_dimensionnement

        peut_analyser = (
            (len(equipements) >= 1 or (len(factures) >= 1 and moyenne is not None))
            and localisation is not None
        )

        if not peut_analyser:
            st.warning("⚠️ Complétez au minimum les étapes **Consommation** (Factures ou Équipements) et **Localisation** avant de lancer l'analyse.")
        else:
            show_pulse = "dim" not in st.session_state
            if show_pulse:
                st.markdown("<div class='btn-pulse'>", unsafe_allow_html=True)
            if st.button("⚡ Lancer l'analyse", type="primary", use_container_width=True):
                with st.spinner("Calcul en cours..."):
                    try:
                        if equipements:
                            dim = calculer_dimensionnement_complet(
                                hsp=localisation["hsp_moyen"],
                                equipements=equipements,
                                module=module,
                                onduleur=onduleur_data,
                                strings=strings,
                                batterie_unitaire=batterie_u
                            )
                        else:
                            dim = calculer_dimensionnement_complet(
                                hsp=localisation["hsp_moyen"],
                                conso_journaliere_kwh=moyenne["consommation_journaliere_moyenne_kwh"],
                                module=module,
                                onduleur=onduleur_data,
                                strings=strings,
                                batterie_unitaire=batterie_u
                            )
                        st.session_state.dim = dim
                        st.success("✅ Analyse terminée !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur : {e}")
            if show_pulse:
                st.markdown("</div>", unsafe_allow_html=True)

        afficher_metriques_dimensionnement()

    # ----------------------------
    # NAVIGATION PRÉCÉDENT / SUIVANT
    # ----------------------------
    st.markdown("<div class='wizard-nav'>", unsafe_allow_html=True)
    col_prev, col_next = st.columns([1, 1])
    with col_prev:
        if step_index > 0:
            if st.button(f"← {WIZARD_STEPS[step_index - 1][1]}", use_container_width=True):
                st.session_state.page_active = WIZARD_STEP_NAMES[step_index - 1]
                st.rerun()
    with col_next:
        if step_index < len(WIZARD_STEPS) - 1:
            if st.button(f"{WIZARD_STEPS[step_index + 1][1]} →", type="primary", use_container_width=True):
                st.session_state.page_active = WIZARD_STEP_NAMES[step_index + 1]
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
