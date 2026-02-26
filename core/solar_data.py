import requests

def geocoder_ville(nom_ville: str) -> dict | None:
    """
        Convertit un nom de ville en coordonnées GPS
        via l'API Nominatim (OpenStreetMap) - 100% gratuite
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": nom_ville,
        "format": "json",
        "limit": 1
    }
    headers = { "User-Agent": "pv-dimensioning-app/1.0"}

    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()

        if not data:
            return None

        results = data[0]
        return {
            "ville": results.get("display_name", nom_ville),
            "latitude": float(results["lat"]),
            "longitude": float(results["lon"])
        }
    except Exception as e:
        print(f"Erreur geocodage : {e}")
        return None


def get_solar_data(latitude:float, longitude:float) -> dict | None:
    """
        Récupère les données d'ensoleillement via l'API PVGIS
        (Commission Européenne) - 100% gratuite
        HSP = Heures de Soleil Pic par jour, donnée clé pour le dimensionnement
    """

    url = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
    params = {
        "lat": latitude,
        "lon": longitude,
        "peakpower": 1,
        "loss": 14,
        "outputformat": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()

        totals = data["outputs"]["totals"]["fixed"]

        # E_d = production journalière moyenne en kWh/kWc → c'est notre HSP
        # E_y = production annuelle totale en kWh/kWc
        # H(i)_d = irradiation journalière moyenne en kWh/m²
        # H(i)_y = irradiation annuelle en kWh/m²

        return {
            "irradiation_annuelle_kwh": round(totals["H(i)_y"], 2),
            "hsp_moyen": round(totals["E_d"], 2),
            "production_annuelle_kwh": round(totals["E_y"], 2),
            "donnees_mensuelles": data["outputs"]["monthly"]["fixed"]
        }
    except Exception as e:
        print(f"Erreur PVGIS : {e}")
        return None
