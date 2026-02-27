import os
import logging
import streamlit as st
import pandas as pd
from pathlib import Path

from core.facture_extractor import extraire_donnees_facture, valider_et_enrichir
from core.storage import (
    ajouter_equipement, get_equipements,
    supprimer_equipement, effacer_equipements,
    sauvegarder_facture, get_factures,
    effacer_factures, get_consommation_moyenne
)

logger = logging.getLogger(__name__)

# ==============================
# CONSTANTES
# ==============================
TAILLE_MAX_UPLOAD_MB = 10
TAILLE_MAX_UPLOAD_OCTETS = TAILLE_MAX_UPLOAD_MB * 1024 * 1024
DOSSIER_FACTURES = Path("data/factures")
EXTENSIONS_VALIDES = {"pdf", "jpg", "jpeg", "png"}


# ==============================
# UTILITAIRES
# ==============================
def _securiser_nom_fichier(nom: str) -> str:
    """
    Nettoie le nom de fichier pour éviter le path traversal.
    Garde uniquement les caractères alphanumériques, tirets, underscores et points.
    """
    nom_path = Path(nom)
    # Garde uniquement le nom de base — supprime tout chemin parent
    nom_base = nom_path.name
    # Remplace les caractères dangereux
    nom_securise = "".join(
        c if c.isalnum() or c in "._-" else "_"
        for c in nom_base
    )
    return nom_securise or "fichier_inconnu"


# ==============================
# FORMULAIRE FACTURES
# ==============================
def afficher_formulaire_factures() -> None:
    """Affiche le formulaire d'upload et d'analyse des factures."""

    st.subheader("📄 Vos factures d'électricité")
    st.write("Uploadez au minimum vos 3 dernières factures pour une analyse précise.")

    # --- Factures déjà extraites ---
    factures_en_base = get_factures()
    if factures_en_base:
        st.success(f"✅ {len(factures_en_base)} facture(s) déjà analysée(s)")

        df = pd.DataFrame(factures_en_base)
        df_affichage = df[[
            "nom_fichier", "periode", "consommation_kwh",
            "consommation_journaliere_kwh", "tarif_moyen"
        ]].copy()
        df_affichage.columns = [
            "Fichier", "Période", "Conso (kWh)",
            "Conso/jour (kWh)", "Tarif moy. (FCFA/kWh)"
        ]
        st.dataframe(df_affichage, use_container_width=True)

        moyenne = get_consommation_moyenne()
        if moyenne:
            col1, col2, col3 = st.columns(3)
            col1.metric(
                "Conso. journalière moyenne",
                f"{moyenne['consommation_journaliere_moyenne_kwh']} kWh/jour"
            )
            col2.metric(
                "Tarif moyen",
                f"{moyenne['tarif_moyen_fcfa_kwh']} FCFA/kWh"
            )
            col3.metric(
                "Nombre de factures",
                str(moyenne['nombre_factures'])
            )

        if st.button("🗑️ Effacer toutes les factures"):
            effacer_factures()
            # Nettoyage des fichiers sur le disque
            if DOSSIER_FACTURES.exists():
                for f in DOSSIER_FACTURES.iterdir():
                    try:
                        f.unlink()
                    except OSError as e:
                        logger.warning("Impossible de supprimer %s : %s", f, e)
            st.rerun()

        st.divider()

    # --- Upload de nouvelles factures ---
    fichiers = st.file_uploader(
        label="Ajouter des factures (PDF ou image)",
        type=list(EXTENSIONS_VALIDES),
        accept_multiple_files=True,
        help=f"Formats acceptés : PDF, JPG, PNG — Taille max : {TAILLE_MAX_UPLOAD_MB} MB"
    )

    if fichiers:
        if len(fichiers) < 3:
            st.warning("⚠️ Nous recommandons au moins 3 factures pour une meilleure précision.")

        if st.button("🔍 Analyser les factures", type="primary"):
            DOSSIER_FACTURES.mkdir(parents=True, exist_ok=True)
            nb_succes = 0
            nb_echec = 0

            for fichier in fichiers:
                # Vérification taille
                contenu = fichier.getbuffer()
                if len(contenu) > TAILLE_MAX_UPLOAD_OCTETS:
                    st.error(
                        f"❌ {fichier.name} trop volumineux "
                        f"(max {TAILLE_MAX_UPLOAD_MB} MB)"
                    )
                    nb_echec += 1
                    continue

                # Sécurisation du nom de fichier
                nom_securise = _securiser_nom_fichier(fichier.name)
                chemin = DOSSIER_FACTURES / nom_securise

                with st.spinner(f"Analyse de {fichier.name} en cours..."):
                    try:
                        # Sauvegarde temporaire sur le disque
                        with open(chemin, "wb") as f:
                            f.write(contenu)

                        # Extraction par le LLM
                        donnees_brutes = extraire_donnees_facture(
                            str(chemin), fichier.name
                        )

                        # Validation et enrichissement Python
                        donnees_validees = valider_et_enrichir(
                            donnees_brutes, fichier.name
                        )

                        if donnees_validees:
                            sauvegarder_facture(donnees_validees)
                            st.success(
                                f"✅ {fichier.name} → "
                                f"{donnees_validees['consommation_kwh']} kWh "
                                f"({donnees_validees['periode']})"
                            )
                            nb_succes += 1
                        else:
                            st.error(
                                f"❌ Impossible d'extraire les données de {fichier.name}"
                            )
                            nb_echec += 1

                    except Exception as e:
                        logger.error("Erreur traitement facture %s : %s", fichier.name, e)
                        st.error(f"❌ Erreur inattendue pour {fichier.name}")
                        nb_echec += 1
                    finally:
                        # Nettoyage du fichier temporaire
                        if chemin.exists():
                            try:
                                chemin.unlink()
                            except OSError:
                                logger.warning("Impossible de supprimer %s", chemin)

            if nb_succes > 0:
                st.info(f"📊 {nb_succes} facture(s) analysée(s) avec succès.")
            st.rerun()


# ==============================
# FORMULAIRE ÉQUIPEMENTS
# ==============================
def afficher_formulaire_equipements() -> None:
    """Affiche le formulaire de saisie des équipements électriques."""

    st.subheader("🔌 Vos équipements électriques")
    st.write("Listez vos appareils pour estimer votre consommation journalière.")

    # --- Formulaire d'ajout ---
    with st.form("form_equipement", clear_on_submit=True):
        nom = st.text_input("Nom de l'appareil", placeholder="Ex: Réfrigérateur")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            puissance = st.number_input("Puissance (W)", min_value=0, step=10)
        with col_b:
            heures = st.number_input(
                "Heures/jour", min_value=0.0, max_value=24.0, step=0.5
            )
        with col_c:
            quantite = st.number_input("Quantité", min_value=1, step=1)

        if st.form_submit_button("➕ Ajouter l'équipement"):
            if nom and nom.strip() and puissance > 0:
                conso = puissance * heures * quantite
                try:
                    ajouter_equipement(
                        nom.strip(), puissance, heures, quantite, conso
                    )
                    st.success(f"✅ {nom.strip()} ajouté !")
                except ValueError as e:
                    st.error(f"❌ {e}")
            else:
                st.error("Veuillez renseigner un nom et une puissance valide.")

    # --- Tableau récapitulatif ---
    equipements = get_equipements()

    if equipements:
        st.write("**Équipements enregistrés :**")

        total_wh = sum(e["conso_jour_wh"] for e in equipements)

        df = pd.DataFrame(equipements)
        df_affichage = df[[
            "nom", "puissance_w", "heures_par_jour", "quantite", "conso_jour_wh"
        ]].copy()
        df_affichage.columns = [
            "Appareil", "Puissance (W)", "Heures/jour", "Quantité", "Conso/jour (Wh)"
        ]
        st.dataframe(df_affichage, use_container_width=True)

        st.metric(
            label="Consommation journalière totale estimée",
            value=f"{total_wh:.0f} Wh/jour",
            delta=f"soit {total_wh / 1000:.2f} kWh/jour"
        )

        # Suppression individuelle
        for e in equipements:
            col_nom, col_suppr = st.columns([5, 1])
            with col_nom:
                st.write(e["nom"])
            with col_suppr:
                if st.button("🗑️", key=f"suppr_{e['id']}"):
                    supprimer_equipement(e["id"])
                    st.rerun()

        if st.button("🗑️ Effacer tous les équipements"):
            effacer_equipements()
            st.rerun()