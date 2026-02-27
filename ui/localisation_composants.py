import logging
import streamlit as st
from core.solar_data import geocoder_ville, get_solar_data
from core.storage import (
    sauvegarder_localisation, get_localisation,
    sauvegarder_onduleur, get_onduleur, effacer_onduleur,
    sauvegarder_module_pv, get_module_pv, effacer_module_pv,
    sauvegarder_batterie, get_batterie, effacer_batterie,
    get_strings, sauvegarder_strings,
    get_parametres, sauvegarder_parametres
)

logger = logging.getLogger(__name__)


# ==============================
# UTILITAIRES
# ==============================
def _valeur_ou_defaut(data: dict, cle: str, defaut: float = 0.0) -> float:
    """Retourne la valeur d'un dict ou un défaut si None."""
    if data and data.get(cle) is not None:
        return float(data[cle])
    return defaut


# ==============================
# LOCALISATION
# ==============================
def afficher_localisation() -> None:
    st.subheader("📍 Localisation du site")

    localisation = get_localisation()
    if localisation:
        st.success(f"📌 Lieu actuel : **{localisation['ville'].split(',')[0]}**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Latitude", f"{localisation['latitude']:.4f}°")
        col2.metric("Longitude", f"{localisation['longitude']:.4f}°")
        col3.metric("HSP moyen", f"{localisation['hsp_moyen']} h/jour")
        st.info(f"☀️ Irradiation annuelle : **{localisation['irradiation_annuelle_kwh']} kWh/m²/an**")
        st.divider()

    st.write("Rechercher un lieu :")
    col_input, col_btn = st.columns([4, 1])

    with col_input:
        ville = st.text_input(
            "Ville",
            placeholder="Ex: Lomé, Abidjan, Dakar...",
            label_visibility="collapsed",
            max_chars=100
        )
    with col_btn:
        rechercher = st.button("🔍 Rechercher", use_container_width=True)

    if rechercher and ville:
        ville = ville.strip()
        if len(ville) < 2:
            st.error("❌ Nom de ville trop court.")
            return

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

        try:
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
        except Exception as e:
            logger.error("Erreur sauvegarde localisation : %s", e)
            st.error("❌ Erreur lors de la sauvegarde.")


# ==============================
# COMPOSANTS
# ==============================
def afficher_composants() -> None:
    """Page configurations avec quatre sous-onglets."""
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
def _formulaire_onduleur() -> None:
    st.subheader("⚡ Caractéristiques de l'onduleur")
    st.write("Ces données permettront de déterminer la configuration des strings et du parc batterie.")

    onduleur = get_onduleur()
    strings = get_strings()

    # --- Infos générales ---
    st.markdown("**Informations générales**")
    st.caption("Tous les champs sont optionnels — plus vous en renseignez, plus les résultats seront précis.")

    col1, col2 = st.columns(2)
    with col1:
        tension_batterie = st.number_input(
            "Tension de démarrage batterie (V)",
            min_value=0.0,
            step=12.0,
            value=_valeur_ou_defaut(onduleur, "tension_demarrage_batterie_v"),
            help="Tension minimale du parc batterie pour démarrer l'onduleur (ex: 24V, 48V)"
        )
    with col2:
        nb_strings = st.selectbox(
            "Nombre d'entrées PV (strings)",
            options=[1, 2],
            index=(onduleur["nb_strings"] - 1) if onduleur and onduleur.get("nb_strings") else 0,
            help="Nombre d'entrées MPPT de l'onduleur"
        )

    if st.button("💾 Sauvegarder les infos générales", type="primary", use_container_width=True):
        try:
            sauvegarder_onduleur(
                tension_demarrage_batterie_v=tension_batterie or None,
                nb_strings=nb_strings
            )
            st.success("✅ Infos générales sauvegardées !")
            st.rerun()
        except Exception as e:
            logger.error("Erreur sauvegarde onduleur : %s", e)
            st.error("❌ Erreur lors de la sauvegarde.")

    st.divider()

    # --- Entrées PV ---
    st.markdown("**Caractéristiques des entrées PV**")
    nb = nb_strings or (onduleur["nb_strings"] if onduleur and onduleur.get("nb_strings") else 1)

    for i in range(1, nb + 1):
        string_data = next((s for s in strings if s["numero_string"] == i), None)

        st.markdown(f"**🔌 Entrée PV {i}**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            voc_max = st.number_input(
                "Voc max (V)", min_value=0.0, step=10.0,
                value=_valeur_ou_defaut(string_data, "voc_max_v"),
                key=f"voc_max_{i}",
                help="Tension en circuit ouvert maximale supportée"
            )
        with col2:
            vmppt_min = st.number_input(
                "Vmppt min (V)", min_value=0.0, step=10.0,
                value=_valeur_ou_defaut(string_data, "vmppt_min_v"),
                key=f"vmppt_min_{i}",
                help="Tension MPPT minimale pour démarrer le tracking"
            )
        with col3:
            vmppt_max = st.number_input(
                "Vmppt max (V)", min_value=0.0, step=10.0,
                value=_valeur_ou_defaut(string_data, "vmppt_max_v"),
                key=f"vmppt_max_{i}",
                help="Tension MPPT maximale pour un fonctionnement optimal"
            )
        with col4:
            imax = st.number_input(
                "Imax (A)", min_value=0.0, step=1.0,
                value=_valeur_ou_defaut(string_data, "imax_a"),
                key=f"imax_{i}",
                help="Courant d'entrée maximal supporté par cette entrée"
            )

        if st.button(f"💾 Sauvegarder entrée PV {i}", key=f"save_string_{i}", use_container_width=True):
            if any([voc_max, vmppt_min, vmppt_max, imax]):
                try:
                    sauvegarder_strings(
                        numero_string=i,
                        voc_max_v=voc_max or None,
                        vmppt_min_v=vmppt_min or None,
                        vmppt_max_v=vmppt_max or None,
                        imax_a=imax or None
                    )
                    st.success(f"✅ Entrée PV {i} sauvegardée !")
                    st.rerun()
                except Exception as e:
                    logger.error("Erreur sauvegarde string %d : %s", i, e)
                    st.error("❌ Erreur lors de la sauvegarde.")
            else:
                st.warning("⚠️ Renseignez au moins une valeur.")

        if i < nb:
            st.markdown("---")

    st.divider()

    # --- Données enregistrées ---
    if onduleur or strings:
        st.markdown("**Données enregistrées**")
        if onduleur:
            col1, col2 = st.columns(2)
            col1.metric("Tension démarrage batterie", f"{onduleur.get('tension_demarrage_batterie_v') or '—'} V")
            col2.metric("Nombre d'entrées PV", str(onduleur.get("nb_strings") or "—"))

        if strings:
            for s in strings:
                st.markdown(f"**🔌 Entrée PV {s['numero_string']}**")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Voc max", f"{s.get('voc_max_v') or '—'} V")
                col2.metric("Vmppt min", f"{s.get('vmppt_min_v') or '—'} V")
                col3.metric("Vmppt max", f"{s.get('vmppt_max_v') or '—'} V")
                col4.metric("Imax", f"{s.get('imax_a') or '—'} A")

        if st.button("🗑️ Effacer tout l'onduleur", use_container_width=True):
            effacer_onduleur()
            st.rerun()


# ==============================
# FORMULAIRE MODULE PV
# ==============================
def _formulaire_module_pv() -> None:
    st.subheader("🔆 Caractéristiques du module PV")
    st.write("Ces données permettront de calculer la configuration série/parallèle et la surface du champ.")

    module = get_module_pv()

    if module:
        st.success("✅ Module PV enregistré")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Puissance crête", f"{module.get('puissance_crete_wc') or '—'} Wc")
        col2.metric("Voc", f"{module.get('voc_v') or '—'} V")
        col3.metric("Isc", f"{module.get('isc_a') or '—'} A")
        col4.metric(
            "Dimensions",
            f"{module['longueur_m']} × {module['largeur_m']} m"
            if module.get("longueur_m") and module.get("largeur_m") else "—"
        )

    st.divider()
    st.write("**Renseignez les caractéristiques de vos modules :**")
    st.caption("Tous les champs sont optionnels.")

    puissance = st.number_input(
        "Puissance crête (Wc)", min_value=0.0, step=10.0,
        value=_valeur_ou_defaut(module, "puissance_crete_wc"),
        help="Puissance maximale du panneau en Watt-crête"
    )

    st.markdown("**Caractéristiques électriques**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        voc = st.number_input("Voc (V)", min_value=0.0, step=1.0,
                              value=_valeur_ou_defaut(module, "voc_v"),
                              help="Tension en circuit ouvert")
    with col2:
        isc = st.number_input("Isc (A)", min_value=0.0, step=0.1,
                              value=_valeur_ou_defaut(module, "isc_a"),
                              help="Courant de court-circuit")
    with col3:
        vmp = st.number_input("Vmp (V)", min_value=0.0, step=1.0,
                              value=_valeur_ou_defaut(module, "vmp_v"),
                              help="Tension au point de puissance maximale")
    with col4:
        imp = st.number_input("Imp (A)", min_value=0.0, step=0.1,
                              value=_valeur_ou_defaut(module, "imp_a"),
                              help="Courant au point de puissance maximale")

    st.markdown("**Dimensions**")
    col_l, col_w = st.columns(2)
    with col_l:
        longueur = st.number_input("Longueur (m)", min_value=0.0, step=0.01,
                                   value=_valeur_ou_defaut(module, "longueur_m"))
    with col_w:
        largeur = st.number_input("Largeur (m)", min_value=0.0, step=0.01,
                                  value=_valeur_ou_defaut(module, "largeur_m"))

    col_save, col_clear = st.columns([3, 1])
    with col_save:
        if st.button("💾 Sauvegarder le module PV", type="primary", use_container_width=True):
            if any([puissance, voc, isc, vmp, imp, longueur, largeur]):
                try:
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
                except Exception as e:
                    logger.error("Erreur sauvegarde module PV : %s", e)
                    st.error("❌ Erreur lors de la sauvegarde.")
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
def _formulaire_batterie() -> None:
    st.subheader("🔋 Caractéristiques de la batterie")
    st.write("Ces données permettront de calculer la configuration du parc batterie.")

    batterie = get_batterie()

    if batterie:
        st.success("✅ Batterie enregistrée")
        col1, col2 = st.columns(2)
        col1.metric("Tension", f"{batterie.get('tension_v') or '—'} V")
        col2.metric("Capacité", f"{batterie.get('capacite_ah') or '—'} Ah")

    st.divider()
    st.write("**Renseignez les caractéristiques de vos batteries :**")
    st.caption("Tous les champs sont optionnels.")

    col1, col2 = st.columns(2)
    with col1:
        tension = st.number_input(
            "Tension nominale (V)", min_value=0.0, step=12.0,
            value=_valeur_ou_defaut(batterie, "tension_v"),
            help="Tension nominale d'une batterie unitaire (ex: 12V, 24V)"
        )
    with col2:
        capacite = st.number_input(
            "Capacité (Ah)", min_value=0.0, step=10.0,
            value=_valeur_ou_defaut(batterie, "capacite_ah"),
            help="Capacité d'une batterie unitaire en Ampère-heure"
        )

    col_save, col_clear = st.columns([3, 1])
    with col_save:
        if st.button("💾 Sauvegarder la batterie", type="primary", use_container_width=True):
            if any([tension, capacite]):
                try:
                    sauvegarder_batterie(
                        tension_v=tension or None,
                        capacite_ah=capacite or None
                    )
                    st.success("✅ Batterie sauvegardée !")
                    st.rerun()
                except Exception as e:
                    logger.error("Erreur sauvegarde batterie : %s", e)
                    st.error("❌ Erreur lors de la sauvegarde.")
            else:
                st.warning("⚠️ Renseignez au moins une caractéristique.")
    with col_clear:
        if batterie:
            if st.button("🗑️ Effacer", use_container_width=True, key="clear_batterie"):
                effacer_batterie()
                st.rerun()


# ==============================
# FORMULAIRE PARAMÈTRES
# ==============================
def _formulaire_parametres() -> None:
    st.subheader("💰 Paramètres économiques")
    st.caption("Ces valeurs sont utilisées pour le calcul de rentabilité.")

    parametres = get_parametres()

    col1, col2 = st.columns(2)
    with col1:
        tarif = st.number_input(
            "Prix du kWh (FCFA)", min_value=0.0, step=5.0,
            value=float(parametres["tarif_kwh"]),
            help="Tarif moyen du kWh. Renseigné automatiquement si des factures sont analysées."
        )
    with col2:
        prix_installation = st.number_input(
            "Prix total de l'installation (FCFA)", min_value=0.0, step=10000.0,
            value=float(parametres["prix_total_installation"]),
            help="Prix total incluant achat des composants et main d'œuvre."
        )

    if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
        try:
            sauvegarder_parametres(tarif, prix_installation)
            st.success("✅ Paramètres sauvegardés !")
            st.rerun()
        except ValueError as e:
            st.error(f"❌ {e}")
        except Exception as e:
            logger.error("Erreur sauvegarde paramètres : %s", e)
            st.error("❌ Erreur lors de la sauvegarde.")

    st.divider()

    if parametres:
        st.markdown("**Paramètres enregistrés :**")
        col1, col2 = st.columns(2)
        col1.metric("Prix du kWh", f"{parametres['tarif_kwh']} FCFA")
        prix = float(parametres["prix_total_installation"])
        col2.metric(
            "Prix installation",
            f"{prix:,.0f} FCFA" if prix > 0 else "Non renseigné"
        )