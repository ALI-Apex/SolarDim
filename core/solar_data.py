import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ==============================
# CONSTANTES
# ==============================
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
PVGIS_URL = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
TIMEOUT_SECONDES = 15
NOM_VILLE_MAX_LONGUEUR = 100
LATITUDE_MIN, LATITUDE_MAX = -90.0, 90.0
LONGITUDE_MIN, LONGITUDE_MAX = -180.0, 180.0


# ==============================
# UTILITAIRES
# ==============================
def _creer_session_avec_retry() -> requests.Session:
    """
    Crée une session HTTP avec retry automatique
    sur les erreurs réseau temporaires.
    """
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


def _valider_nom_ville(nom_ville: str) -> str:
    """Valide et nettoie le nom de ville."""
    if not nom_ville or not isinstance(nom_ville, str):
        raise ValueError("Nom de ville invalide")

    nom_ville = nom_ville.strip()

    if len(nom_ville) < 2:
        raise ValueError("Nom de ville trop court")

    if len(nom_ville) > NOM_VILLE_MAX_LONGUEUR:
        raise ValueError(f"Nom de ville trop long (max {NOM_VILLE_MAX_LONGUEUR} caractères)")

    return nom_ville


def _valider_coordonnees(latitude: float, longitude: float) -> None:
    """Valide les coordonnées GPS."""
    if not (LATITUDE_MIN <= latitude <= LATITUDE_MAX):
        raise ValueError(f"Latitude invalide : {latitude}")
    if not (LONGITUDE_MIN <= longitude <= LONGITUDE_MAX):
        raise ValueError(f"Longitude invalide : {longitude}")


# ==============================
# GÉOCODAGE
# ==============================
def geocoder_ville(nom_ville: str) -> dict | None:
    """
    Convertit un nom de ville en coordonnées GPS
    via l'API Nominatim (OpenStreetMap) — 100% gratuite.
    """
    try:
        nom_ville = _valider_nom_ville(nom_ville)
    except ValueError as e:
        logger.warning("Nom de ville invalide : %s", e)
        return None

    params = {
        "q": nom_ville,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "SolarDim-Pro/1.0 (dimensionnement-pv)"
    }

    try:
        session = _creer_session_avec_retry()
        response = session.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=TIMEOUT_SECONDES
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            logger.info("Aucun résultat pour la ville : %s", nom_ville)
            return None

        result = data[0]
        latitude = float(result["lat"])
        longitude = float(result["lon"])

        _valider_coordonnees(latitude, longitude)

        return {
            "ville": result.get("display_name", nom_ville),
            "latitude": latitude,
            "longitude": longitude
        }

    except requests.exceptions.Timeout:
        logger.error("Timeout Nominatim pour : %s", nom_ville)
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Erreur connexion Nominatim")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error("Erreur HTTP Nominatim : %s", e)
        return None
    except (KeyError, ValueError, IndexError) as e:
        logger.error("Données Nominatim inattendues : %s", e)
        return None
    except Exception as e:
        logger.error("Erreur inattendue géocodage : %s", type(e).__name__)
        return None


# ==============================
# DONNÉES SOLAIRES
# ==============================
def get_solar_data(latitude: float, longitude: float) -> dict | None:
    """
    Récupère les données d'ensoleillement via l'API PVGIS
    (Commission Européenne) — 100% gratuite.

    HSP = Heures de Soleil Pic par jour.
    """
    try:
        _valider_coordonnees(latitude, longitude)
    except ValueError as e:
        logger.warning("Coordonnées invalides : %s", e)
        return None

    params = {
        "lat": latitude,
        "lon": longitude,
        "peakpower": 1,
        "loss": 14,
        "outputformat": "json"
    }

    try:
        session = _creer_session_avec_retry()
        response = session.get(
            PVGIS_URL,
            params=params,
            timeout=TIMEOUT_SECONDES
        )
        response.raise_for_status()
        data = response.json()

        totals = data["outputs"]["totals"]["fixed"]

        # E_d  = production journalière moyenne kWh/kWc → HSP
        # E_y  = production annuelle kWh/kWc
        # H(i)_d = irradiation journalière kWh/m²
        # H(i)_y = irradiation annuelle kWh/m²
        return {
            "irradiation_annuelle_kwh": round(totals["H(i)_y"], 2),
            "hsp_moyen": round(totals["E_d"], 2),
            "production_annuelle_kwh": round(totals["E_y"], 2),
            "donnees_mensuelles": data["outputs"]["monthly"]["fixed"]
        }

    except requests.exceptions.Timeout:
        logger.error("Timeout PVGIS pour lat=%s lon=%s", latitude, longitude)
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Erreur connexion PVGIS")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error("Erreur HTTP PVGIS : %s", e)
        return None
    except KeyError as e:
        logger.error("Structure réponse PVGIS inattendue : %s", e)
        return None
    except Exception as e:
        logger.error("Erreur inattendue PVGIS : %s", type(e).__name__)
        return None