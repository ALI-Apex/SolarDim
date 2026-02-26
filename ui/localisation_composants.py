import streamlit as st
from core.solar_data import geocoder_ville, get_solar_data
from core.storage import (
    sauvegarder_localisation,get_localisation,
    sauvegarder_onduleur, get_onduleur, effacer_onduleur,
    sauvegarder_module_pv, get_module_pv, effacer_module_pv,
    sauvegarder_batterie, get_batterie, effacer_batterie,
)

# --------------- Fonctions Localisation --------------------

def afficher_localisation():
    st.subheader("📍 Localisation du site")

    # Affichage de la localisation déjà sauvegardée
    localisation = get_localisation()
    if localisation:
        st.success(f"📌 Lieu actuel : **{localisation['ville'].split(',')[0]}**")

        col1, col2, col3 = st.columns(3)
        col1.metric("Latitude", f"{localisation['latitude']:.4f}°")
        col2.metric("Longitude", f"{localisation['longitude']:.4f}°")
        col3.metric("HSP moyen", f"{localisation['hsp_moyen']} h/jour")

        st.info(f"☀️ Irradiation annuelle : **{localisation['irradiation_annuelle_kwh']} kWh/m²/an**")
        st.divider()

    # Formulaire de recherche
    st.write("Rechercher un lieu :")
    col_input, col_btn = st.columns([4, 1])

    with col_input:
        ville = st.text_input(
            "Ville",
            placeholder="Ex: Lomé, Abidjan, Dakar...",
            label_visibility="collapsed"
        )
    with col_btn:
        rechercher = st.button("🔍 Rechercher", use_container_width=True)

    if rechercher and ville:

        with st.spinner("Recherche des coordonnées..."):
            coords = geocoder_ville(ville)

        if coords is None:
            st.error("❌ Lieu non trouvé. Essayez un nom plus précis.")
            return

        st.success(f"✅ Lieu trouvé : {coords['ville'].split(',')[0]}")

        with st.spinner("Récupération des données solaires via PVGIS..."):
            solaire = get_solar_data(coords["latitude"], coords["longitude"])

        if solaire is None:
            st.error("❌ Données solaires indisponibles pour ce lieu.")
            return

        sauvegarder_localisation(
            ville=coords["ville"],
            latitude=coords["latitude"],
            longitude=coords["longitude"],
            irradiation_annuelle=solaire["irradiation_annuelle_kwh"],
            hsp_moyen=solaire["hsp_moyen"],
            production_annuelle=solaire["production_annuelle_kwh"]
        )

        st.success("💾 Localisation sauvegardée !")
        st.rerun()

# ----------------- Fonctions composants -----------------------
def  afficher_composants():
    """Page configurations avec quatre sous-onglets"""

    tab_onduleur, tab_module, tab_batterie, tab_params = st.tabs([
        "⚡ Onduleur",
        "🔆 Module PV",
        "🔋 Batterie",
        "💰 Paramètres économiques"
    ])

    with tab_onduleur:
        _formulaire_onduleur()

    with tab_module:
        _formulaire_module_pv()

    with tab_batterie:
        _formulaire_batterie()

    with tab_params:
        _formulaire_parametres()


# ==============================
# FORMULAIRE ONDULEUR
# ==============================
def _formulaire_onduleur():
    from core.storage import (
        get_onduleur,sauvegarder_onduleur, effacer_onduleur,
        get_strings, sauvegarder_strings
    )

    st.subheader("⚡ Caractéristiques de l'onduleur")
    st.write("Ces données permettront de déterminer la configuration des strings et du parc batterie.")

    onduleur = get_onduleur()
    strings = get_strings()

    # =========== FORMULAIRE GENERALE ===================
    st.markdown("**Informations générales**")
    st.caption("Tous les champs sont optionnels — plus vous en renseignez, plus les résultats seront précis.")

    col1, col2 = st.columns(2)

    with col1:
        tension_batterie  = st.number_input(
            "Tension de démarrage batterie (V)",
            min_value=0.0,
            step=12.0,
            value=float(onduleur["tension_demarrage_batterie_v"]) if onduleur and onduleur["tension_demarrage_batterie_v"] else 0.0,
            help="Tension minimale du parc batterie pour démarrer l'onduleur (ex: 24V, 48V)"
        )

        with col2:
            nb_strings  = st.selectbox(
                "Nombre d'entrées PV (strings)",
                options=[1,2],
                index=(onduleur["nb_strings"] -1) if onduleur and onduleur["nb_strings"] else 0,
                help="Nombre d'entrées MPPT de l'onduleur"
            )

        if st.button("💾 Sauvegarder les infos générales", type="primary", use_container_width=True):
            sauvegarder_onduleur(
                tension_demarrage_batterie_v=tension_batterie or None,
                nb_strings=nb_strings,
            )
            st.success("✅ Infos générales sauvegardées !")
            st.rerun()

        st.divider()

    # =========== FORMULAIRE GENERALE ===================
    st.markdown("**Caractéristiques des entrées PV**")

    nb = nb_strings if nb_strings else (onduleur["nb_strings"] if onduleur and onduleur["nb_strings"] else 1)

    for i in range(1, nb + 1):
        # Récupère les données existantes pour cette string
        string_data = next((s for s in strings if s["numero_string"] == i), None)

        st.markdown(f"**🔌 Entrée PV {i}**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            voc_max = st.number_input(
                "Voc max (V)",
                min_value=0.0,
                step=10.0,
                value=float(string_data["voc_max_v"]) if string_data and string_data["voc_max_v"] is not None else 0.0 ,
                key=f"voc_max_{i}",
                help="Tension en circuit ouvert maximale supportée"
            )

        with col2:
            vmppt_min = st.number_input(
                "Vmppt min (V)",
                min_value=0.0,
                step=10.0,
                value=float(string_data["vmppt_min_v"]) if string_data and string_data["vmppt_min_v"] is not None else 0.0 ,
                key=f"vmppt_min_{i}",
                help="Tension MPPT minimale pour démarrer le tracking"
            )

        with col3:
            vmppt_max = st.number_input(
                "Vmppt max (V)",
                min_value=0.0,
                step=10.0,
                value=float(string_data["vmppt_max_v"]) if string_data and string_data["vmppt_max_v"] is not None else 0.0 ,
                key=f"vmppt_max_{i}",
                help="Tension MPPT maximale pour un fonctionnement optimal"
            )

        with col4:
            imax = st.number_input(
                "Imax (A)",
                min_value=0.0,
                step=1.0,
                value=float(string_data["imax_a"]) if string_data and string_data["imax_a"] is not None else 0.0,
                key=f"imax_{i}",
                help="Courant d'entrée maximal supporté par cette entrée"
            )

        if st.button(f"💾 Sauvegarder entrée PV {i}", key=f"save_string_{i}", use_container_width=True):
            if any([voc_max, vmppt_min, vmppt_max, imax]):
                sauvegarder_strings(
                    numero_string=i,
                    voc_max_v=voc_max or None,
                    vmppt_min_v=vmppt_min or None,
                    vmppt_max_v=vmppt_max or None,
                    imax_a=imax or None,
                )
                st.success(f"✅ Entrée PV {i} sauvegardée !")
                st.rerun()
            else:
                st.warning("⚠️ Renseignez au moins une valeur.")

        if i < nb:
            st.markdown("---")

    st.divider()

    # =========== FORMULAIRE GENERALE ===================
    if onduleur or strings:
        st.markdown("**Données enregistrées**")

        if onduleur:
            col1, col2 = st.columns(2)
            col1.metric(
                "Tension démarrage batterie",
                f"{onduleur['tension_demarrage_batterie_v'] or '_'} V"
            )
            col2.metric(
                "Nombre d'entrées PV",
                f"{onduleur['nb_strings'] or '—'}"
            )

        if strings:
            for s in strings:
                st.markdown(f"**🔌 Entrée PV {s['numero_string']}**")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Voc max", f"{s['voc_max_v'] or '—'} V")
                col2.metric("Vmppt min", f"{s['vmppt_min_v'] or '—'} V")
                col3.metric("Vmppt max", f"{s['vmppt_max_v'] or '—'} V")
                col4.metric("Imax", f"{s['imax_a'] or '—'} A")

        if st.button("🗑️ Effacer tout l'onduleur", use_container_width=True):
            effacer_onduleur()
            st.rerun()

# ==============================
# FORMULAIRE MODULE PV
# ==============================
def _formulaire_module_pv():
    st.subheader("🔆 Caractéristiques du module PV")
    st.write("Ces données permettront de calculer la configuration série/parallèle et la surface du champ.")

    module = get_module_pv()

    # Affichage des données sauvegardées
    if module:
        st.success("✅ Module PV enregistré")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Puissance crête", f"{module['puissance_crete_wc'] or '—'} Wc")
        col2.metric("Voc", f"{module['voc_v'] or '—'} V")
        col3.metric("Isc", f"{module['isc_a'] or '—'} A")
        col4.metric("Dimensions",
                    f"{module['longueur_m'] or '—'} × {module['largeur_m'] or '—'} m"
                    if module['longueur_m'] and module['largeur_m'] else "—"
                    )

    st.divider()

    # -------- Formulaire de saisie ------------
    st.write("**Renseignez les caractéristiques de vos modules :**")
    st.caption("Tous les champs sont optionnels — plus vous en renseignez, plus les résultats seront précis.")

    # Puissance crête seule
    puissance = st.number_input(
        "Puissance crête (Wc)",
        min_value=0.0, step=10.0,
        value=float(module["puissance_crete_wc"]) if module and module["puissance_crete_wc"] else 0.0,
        help="Puissance maximale du panneau en Watt-crête"
    )

    st.markdown("**Caractéristiques électriques** *(pour le calcul de configuration)*")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        voc = st.number_input(
            "Voc (V)",
            min_value=0.0, step=1.0,
            value=float(module["voc_v"]) if module and module["voc_v"] else 0.0,
            help="Tension en circuit ouvert"
        )
    with col2:
        isc = st.number_input(
            "Isc (A)",
            min_value=0.0, step=0.1,
            value=float(module["isc_a"]) if module and module["isc_a"] else 0.0,
            help="Courant de court-circuit"
        )
    with col3:
        vmp = st.number_input(
            "Vmp (V)",
            min_value=0.0, step=1.0,
            value=float(module["vmp_v"]) if module and module["vmp_v"] else 0.0,
            help="Tension au point de puissance maximale"
        )
    with col4:
        imp = st.number_input(
            "Imp (A)",
            min_value=0.0, step=0.1,
            value=float(module["imp_a"]) if module and module["imp_a"] else 0.0,
            help="Courant au point de puissance maximale"
        )

    st.markdown("**Dimensions** *(pour le calcul de surface)*")
    col_l, col_w = st.columns(2)
    with col_l:
        longueur = st.number_input(
            "Longueur (m)",
            min_value=0.0, step=0.01,
            value=float(module["longueur_m"]) if module and module["longueur_m"] else 0.0
        )
    with col_w:
        largeur = st.number_input(
            "Largeur (m)",
            min_value=0.0, step=0.01,
            value=float(module["largeur_m"]) if module and module["largeur_m"] else 0.0
        )

    col_save, col_clear = st.columns([3, 1])

    with col_save:
        if st.button("💾 Sauvegarder le module PV", type="primary", use_container_width=True):
            if any([puissance, voc, isc, vmp, imp, longueur, largeur]):
                sauvegarder_module_pv(
                    puissance_crete_wc=puissance or None,
                    voc_v=voc or None,
                    isc_a=isc or None,
                    vmp_v=vmp or None,
                    imp_a=imp or None,
                    longueur_m=longueur or None,
                    largeur_m=largeur or None
                )
                st.success("✅ Module PV sauvegardé !")
                st.rerun()
            else:
                st.warning("⚠️ Renseignez au moins une caractéristique.")

    with col_clear:
        if module:
            if st.button("🗑️ Effacer", use_container_width=True, key="clear_module"):
                effacer_module_pv()
                st.rerun()


# ==============================
# FORMULAIRE BATTERIE
# ==============================
def _formulaire_batterie():
    st.subheader("🔋 Caractéristiques de la batterie")
    st.write("Ces données permettront de calculer la configuration du parc batterie.")

    batterie = get_batterie()

    # Affichage des données sauvegardées
    if batterie:
        st.success("✅ Batterie enregistrée")
        col1, col2 = st.columns(2)
        col1.metric("Tension", f"{batterie['tension_v'] or '—'} V")
        col2.metric("Capacité", f"{batterie['capacite_ah'] or '—'} Ah")

    st.divider()

    # Formulaire de saisie
    st.write("**Renseignez les caractéristiques de vos batteries :**")
    st.caption("Tous les champs sont optionnels.")

    col1, col2 = st.columns(2)

    with col1:
        tension = st.number_input(
            "Tension nominale (V)",
            min_value=0.0, step=12.0,
            value=float(batterie["tension_v"]) if batterie and batterie["tension_v"] else 0.0,
            help="Tension nominale d'une batterie unitaire (ex: 12V, 24V)"
        )

    with col2:
        capacite = st.number_input(
            "Capacité (Ah)",
            min_value=0.0, step=10.0,
            value=float(batterie["capacite_ah"]) if batterie and batterie["capacite_ah"] else 0.0,
            help="Capacité d'une batterie unitaire en Ampère-heure"
        )

    col_save, col_clear = st.columns([3, 1])

    with col_save:
        if st.button("💾 Sauvegarder la batterie", type="primary", use_container_width=True):
            if any([tension, capacite]):
                sauvegarder_batterie(
                    tension_v=tension or None,
                    capacite_ah=capacite or None
                )
                st.success("✅ Batterie sauvegardée !")
                st.rerun()
            else:
                st.warning("⚠️ Renseignez au moins une caractéristique.")

    with col_clear:
        if batterie:
            if st.button("🗑️ Effacer", use_container_width=True, key="clear_batterie"):
                effacer_batterie()
                st.rerun()

# ==============================
# FORMULAIRE parametres
# ==============================

def _formulaire_parametres():
    from core.storage import get_parametres, sauvegarder_parametres

    st.subheader("💰 Paramètres économiques")
    st.caption("Ces valeurs sont utilisées pour le calcul de rentabilité.")

    parametres = get_parametres()

    col1, col2 = st.columns(2)

    with col1:
        tarif = st.number_input(
            "Prix du kwh (FCFA)",
            min_value=0.0,
            step=5.0,
            value=float(parametres["tarif_kwh"]),
            help="Tarif moyen du kWh. Renseigné automatiquement si des factures sont analysées."
        )

    with col2:
        prix_installation = st.number_input(
            "Prix total de l'installation (FCFA)",
            min_value=0.0,
            step=10000.0,
            value=float(parametres["prix_total_installation"]),
            help="Prix total incluant achat des composants et main d'oeuvre."
        )

    if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
        sauvegarder_parametres(tarif, prix_installation)
        st.success("✅ Paramètres sauvegardés !")
        st.rerun()

    st.divider()

    # Affichage des valeurs actuelles
    if parametres:
        st.markdown("**Paramètres enregistrés :**")
        col1, col2 = st.columns(2)
        col1.metric("Prix du kwh", f"{parametres['tarif_kwh']} FCFA")
        col2.metric(
            "Prix installation",
            f"{float(parametres["prix_total_installation"]):,.0f} FCFA"
            if float(parametres["prix_total_installation"]) > 0 else "Non renseigné"
        )
