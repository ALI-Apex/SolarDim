import os
import streamlit as st
import pandas as pd

from core.facture_extractor import (
    extraire_donnees_facture,
    valider_et_enrichir
)
from core.storage import (
    ajouter_equipement, get_equipements,
    supprimer_equipement, effacer_equipements,
    sauvegarder_facture, get_factures,
    effacer_factures, get_consommation_moyenne
)

def afficher_formulaire_factures():
    st.subheader("📄 Vos factures d'électricité")
    st.write("Uploadez au minimum vos 3 dernières factures pour une analyse précise.")

    # Affichage des factures déjà extraites
    factures_en_base = get_factures()
    if factures_en_base:
        st.success(f"✅ {len(factures_en_base)} facture(s) déjà analysée(s)")

        df = pd.DataFrame(factures_en_base)
        df_affichage = df[[
            "nom_fichier", "periode", "consommation_kwh",
            "consommation_journaliere_kwh", "tarif_moyen"
        ]]
        df_affichage.columns = [
            "Fichier", "Période", "Conso (kWh)",
            "Conso/jour (kWh)", "Tarif moy. (FCFA/kWh)"
        ]
        st.dataframe(df_affichage, width='stretch')

        # Affichage de la moyenne
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
                f"{moyenne['nombre_factures']}"
            )

        if st.button("🗑️ Effacer toutes les factures"):
            effacer_factures()
            st.rerun()

        st.divider()

    # Upload de nouvelles factures
    fichiers = st.file_uploader(
        label="Ajouter des factures (PDF ou image)",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Formats acceptés : PDF, JPG, PNG"
    )

    if fichiers:
        if len(fichiers) < 3:
            st.warning("⚠️ Nous recommandons au moins 3 factures.")

        if st.button("🔍 Analyser les factures", type="primary"):
            # Création du dossier de stockage
            os.makedirs("data/factures", exist_ok=True)

            for fichier in fichiers:
                with st.spinner(f"Analyse de {fichier.name} en cours..."):

                    # Sauvegarde du fichier sur le disque
                    chemin = f"data/factures/{fichier.name}"
                    with open(chemin, "wb") as f:
                        f.write(fichier.getbuffer())

                    # Extraction par le LLM
                    donnees_brutes = extraire_donnees_facture(chemin, fichier.name)

                    # Validation et enrichissement par Python
                    donnees_validees = valider_et_enrichir(donnees_brutes, fichier.name)

                    if donnees_validees:
                        sauvegarder_facture(donnees_validees)
                        st.success(f"✅ {fichier.name} → {donnees_validees['consommation_kwh']} kWh ({donnees_validees['periode']})")
                    else:
                        st.error(f"❌ Impossible d'extraire les données de {fichier.name}")

            st.rerun()


def afficher_formulaire_equipements():
    """Section saisie manuelle des équipements"""

    st.subheader("🔌 Vos équipements électriques")
    st.write("Listez vos appareils pour estimer votre consommation journalière.")

    # Formulaire d'ajout d'équipements :
    with st.form("form_equipement", clear_on_submit= True):
        # clear_on_submit vide les champs apres soumission
        nom = st.text_input("Nom de l'appareil", placeholder="Ex: Réfrigérateur")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            puissance = st.number_input("Puissance (W)", min_value=0, step=10)

        with col_b:
            heures = st.number_input("Heures/jour", min_value=0.0, max_value=24.0, step=0.5)

        with col_c:
            quantite = st.number_input("Quantité", min_value=1, step=1)

        ajouter = st.form_submit_button("➕ Ajouter l'équipement")

        if ajouter:
            if nom and puissance > 0:
                conso = puissance * heures * quantite
                # on sauvegarde dans notre BD
                ajouter_equipement(nom, puissance, heures, quantite, conso)
                st.success(f"✅ {nom} ajouté !")

            else:
                st.error("Veuillez renseigner un nom et une puissance valide.")

    # ---- Tableau récapitulatif des elements saisies -------
    # on relit depuis la base pour avoir des donnees fraiches
    equipements = get_equipements()

    if  equipements:
        st.write("**Équipements enregistrés :**")

        # Calcul du total
        total_wh = sum(e["conso_jour_wh"] for e in equipements)

        df = pd.DataFrame(equipements)
        # On n'affiche pas les colonnes techniques id et created_at
        df_affichage = df[["nom", "puissance_w", "heures_par_jour", "quantite", "conso_jour_wh"]]
        df_affichage.columns = ["Appareil", "Puissance (W)", "Heures/jour", "Quantité", "Conso/jour (Wh)"]
        st.dataframe(df_affichage, width="stretch")

        st.metric(
            label="Consommation journalière totale estimée",
            value=f"{total_wh:.0f} Wh/jour",
            delta=f"soit {total_wh / 1000:.2f} kWh/jour"
        )

        # Supprimer un equipement
        for e in equipements:
            col_nom, col_suppr = st.columns([5,1])
            with col_nom:
                st.write(e["nom"])
            with col_suppr:
                if st.button("🗑️", key=f"suppr_{e['id']}"):
                    supprimer_equipement(e["id"])
                    st.rerun()

        # Bouton pour vider la liste
        if st.button("🗑️ Effacer tous les équipements"):
            effacer_equipements()
            st.rerun() # force streamlit a executer le script immédiatement

    return equipements
