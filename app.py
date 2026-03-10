import traceback

import streamlit as st
from ui.style import get_css
from core.storage import initialiser_stockage

st.set_page_config(
    page_title="SolarDim Pro",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown(get_css(), unsafe_allow_html=True)
initialiser_stockage()

if "page_active" not in st.session_state:
    st.session_state.page_active = "Accueil"

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("""
        <div style='text-align:center; padding: 20px 0 20px 0;'>
            <div style='font-size:48px;'></div>
            <div style='font-size:32px; font-weight:bold; color:white;'>SolarDim</div>
            <div style='font-size:16px; color:vert;'>Fahishal</div>
        </div>
    """, unsafe_allow_html=True)

    pages = [
        ("🏠", "Accueil"),
        ("📄", "Factures"),
        ("🔌", "Équipements"),
        ("📍", "Localisation"),
        ("🔧", "Configurations"),
        ("🤖", "Analyse IA"),
        ("📖", "Guide & Notions")
    ]

    if "page_active" not in st.session_state:
        st.session_state.page_active = "Accueil"

    # Correction si l'ancien nom est en mémoire
    noms_valides = [nom for _, nom in pages]
    if st.session_state.page_active not in noms_valides:
        st.session_state.page_active = "Accueil"

    for icone, nom in pages:
        if st.button(
            f"{icone}  {nom}",
            key=f"nav_{nom}",
            use_container_width=True
        ):
            st.session_state.page_active = nom
            st.rerun()

    # CSS dynamique pour le bouton actif
    noms_pages = [nom for _, nom in pages]
    index_actif = noms_pages.index(st.session_state.page_active)
    icone_actif, nom_actif = pages[index_actif]

    st.markdown(f"""
        <style>
        [data-testid="stSidebar"] .stButton > button:has(div:contains("{icone_actif}  {nom_actif}")) {{
            background-color: #F4A300 !important;
            color: white !important;
            font-weight: bold !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# ==============================
# CONTENU PRINCIPAL
# ==============================
page = st.session_state.page_active

# ----------------------------
# ACCUEIL
# ----------------------------
if page == "Accueil":
    from core.storage import (
        get_factures, get_equipements, get_localisation,
        get_consommation_moyenne, get_module_pv,
        get_onduleur, get_batterie, get_strings
    )

    from core.sizing import (
        calculer_dimensionnement_complet,
        calculer_consommation_journaliere
    )
    from ui.results_display import afficher_metriques_dimensionnement

    # Récupération de toutes les données
    factures = get_factures()
    equipements = get_equipements()
    localisation = get_localisation()
    moyenne = get_consommation_moyenne()
    module = get_module_pv()
    onduleur_data = get_onduleur()
    batterie_u = get_batterie()

    st.markdown("<div class='page-title'>Tableau de bord</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Renseignez vos données puis lancez l'analyse</div>", unsafe_allow_html=True)

    # --- KPI Cards ---
    col1, col2, col3, col4 = st.columns(4)

    conso_moy = f"{moyenne['consommation_journaliere_moyenne_kwh']} kWh/j" if moyenne else "—"
    tarif_moy = f"{moyenne['tarif_moyen_fcfa_kwh']} FCFA/kWh" if moyenne else "—"
    hsp = f"{localisation['hsp_moyen']} h/j" if localisation else "—"
    ville = localisation['ville'].split(',')[0] if localisation else "Non définie"
    nb_eq = len(equipements)
    conso_eq_wh = calculer_consommation_journaliere(equipements) if equipements else 0
    conso_eq_kwh = round(conso_eq_wh / 1000, 2) if equipements else 0

    with col1:
        statut = f"✓ {len(factures)} facture(s)" if factures else (
            "✓ Depuis équipements" if equipements else "⚠ Non renseigné"
        )
        st.markdown(f"""
            <div class='metric-card blue'>
                <div class='label'>Consommation moyenne</div>
                <div class='value'>{conso_moy}</div>
                <div class='status-ok'>{statut}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='label'>Tarif moyen</div>
                <div class='value'>{tarif_moy}</div>
                <div class='status-ok'>{'✓ Calculé' if moyenne else '⚠ Non disponible'}</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='label'>HSP — {ville}</div>
                <div class='value'>{hsp}</div>
                <div class='status-ok'>{'✓ PVGIS' if localisation else '⚠ Localisation manquante'}</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class='metric-card blue'>
                <div class='label'>Énergie journalière EQ</div>
                <div class='value'>{conso_eq_kwh if conso_eq_kwh > 0 else "—"} kWh/j</div>
                <div class='{"status-ok" if conso_eq_kwh > 0 else "status-error"}'>
                    {'✓ ' + str(nb_eq) + ' équipement(s) saisi(s)' if nb_eq > 0 else '⚠ Aucun équipement'}
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Checklist ---
    has_conso = len(factures) >= 1 or len(equipements) >= 1
    has_composants = any([module, onduleur_data, batterie_u])

    st.subheader("📋 Checklist")

    etapes = [
        ("Consommation renseignée (factures ou équipements)", has_conso, "Factures"),
        ("Localisation définie", localisation is not None, "Localisation"),
        ("Composants renseignés (optionnel)", has_composants, "Configurations"),
    ]

    cols = st.columns(len(etapes))
    for i, (label, ok, page_cible) in enumerate(etapes):
        with cols[i]:
            icone = "✅" if ok else ("⚠️" if "optionnel" in label else "❌")
            st.markdown(f"{icone} {label}")
            if not ok:
                if st.button("→ Aller", key=f"goto_{page_cible}"):
                    st.session_state.page_active = page_cible
                    st.rerun()

    st.markdown("---")

    # --- Bouton lancer l'analyse ---
    peut_analyser = has_conso and localisation is not None

    # recuperation des donnees
    module = get_module_pv()
    onduleur_data = get_onduleur()
    strings = get_strings()
    batterie_u = get_batterie()

    if peut_analyser:
        if st.button("⚡ Lancer l'analyse", type="primary", use_container_width=True):
            with st.spinner("Calcul en cours..."):
                try:
                    # Calcul Python du dimensionnement pour métriques et graphes
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

    else:
        st.warning("⚠️ Renseignez au minimum votre consommation et votre localisation.")

    # --- Résultats + Graphe + Fiche technique ---
    afficher_metriques_dimensionnement()

# ----------------------------
# FACTURES
# ----------------------------
elif page == "Factures":
    st.markdown("<div class='page-title'>📄 Factures d'électricité</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Uploadez et analysez vos factures</div>", unsafe_allow_html=True)
    from ui.input_forms import afficher_formulaire_factures
    afficher_formulaire_factures()

# ----------------------------
# ÉQUIPEMENTS
# ----------------------------
elif page == "Équipements":
    st.markdown("<div class='page-title'>🔌 Équipements électriques</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Listez vos appareils pour estimer votre consommation</div>", unsafe_allow_html=True)
    from ui.input_forms import afficher_formulaire_equipements
    afficher_formulaire_equipements()

# ----------------------------
# LOCALISATION
# ----------------------------
elif page == "Localisation":
    st.markdown("<div class='page-title'>📍 Localisation du site</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Données d'ensoleillement via PVGIS</div>", unsafe_allow_html=True)
    from ui.localisation_composants import afficher_localisation
    afficher_localisation()

# ----------------------------
# COMPOSANTS
# ----------------------------
elif page == "Configurations":
    st.markdown("<div class='page-title'>🔧 Configurations</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Renseignez vos composants et les paramètres économiques</div>", unsafe_allow_html=True)
    from ui.localisation_composants import afficher_composants
    afficher_composants()

# ----------------------------
# ANALYSE IA
# ----------------------------
elif page == "Analyse IA":
    st.markdown("<div class='page-title'>🤖 Analyse IA</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Rapport complet généré par l'agent</div>", unsafe_allow_html=True)
    from ui.results_display import afficher_rapport_agent
    afficher_rapport_agent()

# ----------------------------
# GUIDE & NOTIONS
# ----------------------------
elif page == "Guide & Notions":
    st.markdown("<div class='page-title'>📖 Guide & Notions</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Comprendre les concepts et utiliser l'outil efficacement</div>", unsafe_allow_html=True)
    from ui.guide import afficher_guide
    afficher_guide()