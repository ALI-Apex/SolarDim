import html
import logging
import tempfile
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

TAILLE_MAX_UPLOAD_MB = 10
TAILLE_MAX_UPLOAD_OCTETS = TAILLE_MAX_UPLOAD_MB * 1024 * 1024
EXTENSIONS_VALIDES = {"pdf", "jpg", "jpeg", "png"}


def _securiser_nom_fichier(nom: str) -> str:
    nom_base = Path(nom).name
    nom_securise = "".join(
        c if c.isalnum() or c in "._-" else "_"
        for c in nom_base
    )
    return nom_securise or "fichier_inconnu"


def afficher_formulaire_factures() -> None:
    st.subheader("📄 Vos factures d'électricité")
    st.write("Uploadez au minimum vos 3 dernières factures pour une analyse précise.")

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
            st.markdown(f"""
            <div class='kpi-row' style='grid-template-columns: repeat(3, 1fr);'>
                <div class='kpi-card light'>
                    <div class='kpi-label'>Conso. journalière moyenne</div>
                    <div class='kpi-value'>{moyenne['consommation_journaliere_moyenne_kwh']} kWh/j</div>
                </div>
                <div class='kpi-card light'>
                    <div class='kpi-label'>Tarif moyen</div>
                    <div class='kpi-value'>{moyenne['tarif_moyen_fcfa_kwh']} FCFA</div>
                    <div class='kpi-sub'>par kWh</div>
                </div>
                <div class='kpi-card dark'>
                    <div class='kpi-label'>Factures analysées</div>
                    <div class='kpi-value'>{moyenne['nombre_factures']}</div>
                    <div class='kpi-sub'>✓ Données exploitables</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑️ Effacer toutes les factures"):
            effacer_factures()
            st.rerun()

        st.divider()

    fichiers = st.file_uploader(
        label="📂 Glissez-déposez vos factures ici ou cliquez pour sélectionner",
        type=list(EXTENSIONS_VALIDES),
        accept_multiple_files=True,
        help=f"Formats acceptés : PDF, JPG, PNG — Taille max : {TAILLE_MAX_UPLOAD_MB} MB"
    )

    if fichiers:
        if len(fichiers) < 3:
            st.warning("⚠️ Nous recommandons au moins 3 factures pour une meilleure précision.")

        if st.button("🔍 Analyser les factures", type="primary"):
            nb_succes = 0
            nb_echec = 0

            for fichier in fichiers:
                contenu = fichier.getbuffer()

                if len(contenu) > TAILLE_MAX_UPLOAD_OCTETS:
                    st.error(f"❌ {fichier.name} trop volumineux (max {TAILLE_MAX_UPLOAD_MB} MB)")
                    nb_echec += 1
                    continue

                extension = Path(_securiser_nom_fichier(fichier.name)).suffix.lower()
                chemin_temp = None

                with st.spinner(f"Analyse de {fichier.name} en cours..."):
                    try:
                        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
                            tmp.write(contenu)
                            chemin_temp = Path(tmp.name)

                        donnees_brutes = extraire_donnees_facture(str(chemin_temp), fichier.name)
                        donnees_validees = valider_et_enrichir(donnees_brutes, fichier.name)

                        if donnees_validees:
                            sauvegarder_facture(donnees_validees)
                            st.success(
                                f"✅ {fichier.name} → "
                                f"{donnees_validees['consommation_kwh']} kWh "
                                f"({donnees_validees['periode']})"
                            )
                            nb_succes += 1
                        else:
                            st.error(f"❌ Impossible d'extraire les données de {fichier.name}")
                            nb_echec += 1

                    except Exception as e:
                        logger.error("Erreur traitement facture %s : %s", fichier.name, e)
                        st.error(f"❌ Erreur inattendue pour {fichier.name}")
                        nb_echec += 1
                    finally:
                        if chemin_temp and chemin_temp.exists():
                            chemin_temp.unlink(missing_ok=True)

            if nb_succes > 0:
                st.info(f"📊 {nb_succes} facture(s) analysée(s) avec succès.")
            st.rerun()


def afficher_formulaire_equipements() -> None:
    if st.session_state.get("_equipement_added"):
        del st.session_state["_equipement_added"]
        st.rerun()

    equipements = get_equipements()
    total_wh = sum(e["conso_jour_wh"] for e in equipements) if equipements else 0
    total_kwh = round(total_wh / 1000, 2)
    nb = len(equipements)

    # --- Compteur live ---
    st.markdown(f"""
    <div class='consumption-counter'>
        <div class='cc-left'>
            <div class='cc-label'>Consommation totale estimée</div>
            <div class='cc-total'>{total_wh:,.0f} <span style='font-size:16px;font-weight:normal'>Wh/j</span></div>
        </div>
        <div class='cc-right'>
            <div class='cc-kwh'>{total_kwh} kWh/j</div>
            <div class='cc-count'>{'✓ ' + str(nb) + ' appareil(s)' if nb > 0 else '⚠ Aucun appareil'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Formulaire ajout ---
    with st.form("form_equipement", clear_on_submit=True):
        col_nom, col_w, col_h, col_q, col_btn = st.columns([3, 1.5, 1.5, 1, 1.5])
        with col_nom:
            nom = st.text_input("Appareil", placeholder="Ex: Réfrigérateur", label_visibility="collapsed")
        with col_w:
            puissance = st.number_input("W", min_value=0, step=10, label_visibility="collapsed")
        with col_h:
            heures = st.number_input("h/j", min_value=0.0, max_value=24.0, step=0.5, label_visibility="collapsed")
        with col_q:
            quantite = st.number_input("Qté", min_value=1, step=1, label_visibility="collapsed")
        with col_btn:
            submit = st.form_submit_button("➕ Ajouter", use_container_width=True)

        if submit:
            if nom and nom.strip() and puissance > 0:
                conso = puissance * heures * quantite
                try:
                    ajouter_equipement(nom.strip(), puissance, heures, quantite, conso)
                    st.success(f"✅ {nom.strip()} ajouté !")
                    st.session_state["_equipement_added"] = True
                except ValueError as e:
                    st.error(f"❌ {e}")
            else:
                st.error("Veuillez renseigner un nom et une puissance > 0.")

    # --- Tableau des équipements ---
    if equipements:
        st.markdown("**Équipements enregistrés :**")

        header_cols = st.columns([3, 1.5, 1.5, 1, 1.5, 0.8])
        headers = ["Appareil", "Puissance (W)", "Heures/jour", "Qté", "Conso (Wh/j)", ""]
        for col, h in zip(header_cols, headers):
            col.markdown(f"<div style='font-size:12px;color:#888;font-weight:600'>{h}</div>", unsafe_allow_html=True)

        for e in equipements:
            row_cols = st.columns([3, 1.5, 1.5, 1, 1.5, 0.8])
            row_cols[0].write(e["nom"])
            row_cols[1].write(str(e["puissance_w"]))
            row_cols[2].write(str(e["heures_par_jour"]))
            row_cols[3].write(str(e["quantite"]))
            row_cols[4].markdown(f"**{e['conso_jour_wh']:,.0f}**")
            if row_cols[5].button("✕", key=f"suppr_{e['id']}", help="Supprimer"):
                supprimer_equipement(e["id"])
                st.rerun()

        st.markdown("---")

        if total_wh > 0:
            st.markdown("**Répartition de la consommation :**")
            colors = ["#1B2A4A", "#F4A300", "#27AE60", "#E74C3C", "#9B59B6", "#16A085"]
            for i, e in enumerate(sorted(equipements, key=lambda x: x["conso_jour_wh"], reverse=True)):
                pct = round(e["conso_jour_wh"] / total_wh * 100, 1)
                color = colors[i % len(colors)]
                st.markdown(f"""
                <div class='distrib-bar-container'>
                    <div class='distrib-bar-header'>
                        <span>{html.escape(e['nom'])}</span><span>{pct}%</span>
                    </div>
                    <div class='distrib-bar-track'>
                        <div class='distrib-bar-fill' style='width:{pct}%; background:{color}'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Effacer tous les équipements"):
            effacer_equipements()
            st.rerun()