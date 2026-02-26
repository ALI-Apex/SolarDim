from langchain.tools import tool
from core.storage import  get_equipements, get_localisation, get_composants
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
def outil_dimensionnement(puissance_panneau_wc: float = 400, tension_batterie_v: float = 24) -> dict:
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
def outil_rentabilite(puissance_installee_kwc: float, tarif_kwh: float = 0.15) -> dict:
    """
    Calcule l'étude de rentabilité sur 20 ans.

    Paramètres :
    - puissance_installee_kwc : puissance totale installée en kWc
    - tarif_kwh               : prix du kWh en devise locale (défaut 0.15)
    """
    localisation = get_localisation()
    if not localisation:
        return {"erreur": "Localisation manquante."}

    production_annuelle = localisation["irradiation_annuelle_kwh"] * puissance_installee_kwc

    return calculer_rentabilite(
        puissance_installee_kwc=puissance_installee_kwc,
        production_annuelle_kwh=production_annuelle,
        tarif_kwh=tarif_kwh
    )