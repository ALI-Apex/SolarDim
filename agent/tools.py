from langchain.tools import tool
from config import TARIF_KWH_DEFAULT_FCFA, PUISSANCE_PANNEAU_DEFAULT_WC, TENSION_BATTERIE_DEFAULT_V
from core.storage import get_equipements, get_localisation, get_composants, get_parametres
from core.sizing import (
    calculer_dimensionnement_complet,
    calculer_rentabilite
)

@tool
def get_donnees_projet(input: str = "") -> dict:
    """
    Récupère toutes les données du projet depuis la base de données :
    équipements saisis par l'utilisateur, localisation et composants disponibles.
    Appelle cet outil en premier avant tout calcul.
    """
    equipements = get_equipements()
    localisation = get_localisation()
    composants = get_composants()

    return {
        "equipements": equipements,
        "localisation": localisation,
        "composants": composants,
        "nombre_equipements": len(equipements),
        "consommation_totale_wh": sum(e["conso_jour_wh"] for e in equipements)
    }


@tool
def outil_dimensionnement(puissance_panneau_wc: float = PUISSANCE_PANNEAU_DEFAULT_WC, tension_batterie_v: float = TENSION_BATTERIE_DEFAULT_V) -> dict:
    """
    Calcule le dimensionnement complet du système PV off-grid.
    Utilise les données de la base (équipements + localisation).

    Paramètres :
    - puissance_panneau_wc : puissance unitaire du panneau en Wc (défaut 400)
    - tension_batterie_v   : tension du parc batterie en V (12, 24 ou 48)
    """
    equipements = get_equipements()
    localisation = get_localisation()

    if not equipements:
        return {"erreur": "Aucun équipement trouvé dans la base de données."}
    if not localisation:
        return {"erreur": "Aucune localisation trouvée dans la base de données."}

    hsp = localisation["hsp_moyen"]

    dimensionnement = calculer_dimensionnement_complet(
        equipements=equipements,
        hsp=hsp,
        puissance_panneau_wc=puissance_panneau_wc,
        tension_batterie_v=tension_batterie_v
    )


    return dimensionnement


@tool
def outil_rentabilite(puissance_installee_kwc: float, tarif_kwh: float = TARIF_KWH_DEFAULT_FCFA) -> dict:
    """
    Calcule l'étude de rentabilité sur 10 ans.

    Paramètres :
    - puissance_installee_kwc : puissance totale installée en kWc
    - tarif_kwh               : prix du kWh en FCFA (défaut 150)
    """
    localisation = get_localisation()
    if not localisation:
        return {"erreur": "Localisation manquante."}

    parametres = get_parametres()
    production_annuelle = localisation["irradiation_annuelle_kwh"] * puissance_installee_kwc

    return calculer_rentabilite(
        prix_total_installation=float(parametres["prix_total_installation"]),
        production_annuelle_kwh=production_annuelle,
        tarif_kwh=tarif_kwh
    )