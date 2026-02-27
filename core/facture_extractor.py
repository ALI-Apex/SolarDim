import os
import json
import base64
import logging
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import fitz

load_dotenv()

logger = logging.getLogger(__name__)

# ==============================
# CONSTANTES
# ==============================
EXTENSIONS_IMAGES = {"jpg", "jpeg", "png"}
EXTENSIONS_VALIDES = EXTENSIONS_IMAGES | {"pdf"}
TAILLE_MAX_OCTETS = 10 * 1024 * 1024  # 10 MB
CONSO_MIN_KWH = 10
CONSO_MAX_KWH = 10000
MONTANT_MIN_FCFA = 1000
MONTANT_MAX_FCFA = 2_000_000
MODEL_VISION = "meta-llama/llama-4-scout-17b-16e-instruct"
MODEL_TEXTE = "llama-3.3-70b-versatile"

PROMPT_EXTRACTION = """Tu es un expert en lecture de factures d'électricité.

Analyse cette facture et extrais UNIQUEMENT les informations suivantes.
Réponds UNIQUEMENT avec un JSON valide, sans texte avant ou après.

Format de réponse attendu :
{
    "periode": "Mois Année (ex: Novembre 2025)",
    "duree_jours": nombre de jours de la période,
    "consommation_kwh": consommation totale en kWh,
    "puissance_souscrite_kva": puissance souscrite en kVA,
    "montant_ttc": montant total TTC en devise locale,
    "fournisseur": "nom du fournisseur d'électricité",
    "usage": "type d'usage (Domestique, Commercial, etc)"
}

Règles importantes :
- Si une information n'est pas visible, mets null
- Ne fais aucun calcul, extrais uniquement ce qui est écrit
- Les nombres doivent être des valeurs numériques, pas des chaînes
- Ignore les impayés et les rappels, concentre-toi sur la facture du mois en cours
- Retourne TOUJOURS les nombres sans séparateurs de milliers
  Ex: "166.707 FCFA" doit être retourné comme 166707
  Ex: "1.194 kWh" doit être retourné comme 1194
- Une consommation mensuelle normale est entre 50 et 5000 kWh
- Un montant de facture normal est entre 5000 et 500000 FCFA"""


# ==============================
# UTILITAIRES
# ==============================
def _valider_chemin_fichier(chemin: str) -> Path:
    """Valide et sécurise le chemin du fichier."""
    path = Path(chemin).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    if path.stat().st_size > TAILLE_MAX_OCTETS:
        raise ValueError(f"Fichier trop volumineux (max {TAILLE_MAX_OCTETS // 1024 // 1024} MB)")

    extension = path.suffix.lower().lstrip(".")
    if extension not in EXTENSIONS_VALIDES:
        raise ValueError(f"Extension non supportée : {extension}")

    return path


def _image_en_base64(chemin: Path) -> str:
    """Convertit une image en base64."""
    with open(chemin, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _nettoyer_json(texte: str) -> str:
    """Nettoie la réponse LLM pour extraire le JSON."""
    if "```json" in texte:
        texte = texte.split("```json")[1].split("```")[0]
    elif "```" in texte:
        texte = texte.split("```")[1].split("```")[0]
    return texte.strip()


def _creer_llm(model: str) -> ChatGroq:
    """Crée une instance LLM avec la clé API."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY non définie dans les variables d'environnement")
    return ChatGroq(model=model, api_key=api_key, temperature=0)


# ==============================
# EXTRACTION
# ==============================
def _extraire_depuis_image(chemin: Path) -> dict | None:
    """Extrait les données d'une facture image."""
    extension = chemin.suffix.lower().lstrip(".")
    media_type = "image/png" if extension == "png" else "image/jpeg"

    image_b64 = _image_en_base64(chemin)
    llm = _creer_llm(MODEL_VISION)

    message = HumanMessage(content=[
        {"type": "text", "text": PROMPT_EXTRACTION},
        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}}
    ])

    reponse = llm.invoke([message])
    return json.loads(_nettoyer_json(reponse.content.strip()))


def _extraire_depuis_pdf(chemin: Path) -> dict | None:
    """Extrait les données d'une facture PDF."""
    doc = fitz.open(str(chemin))
    texte = "".join(page.get_text() for page in doc)
    doc.close()

    if not texte.strip():
        # PDF scanné → conversion en image temporaire (une seule fois, pas de récursion)
        logger.info("PDF sans texte détecté — conversion en image")
        doc = fitz.open(str(chemin))
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        doc.close()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            chemin_temp = Path(tmp.name)

        try:
            pix.save(str(chemin_temp))
            return _extraire_depuis_image(chemin_temp)
        finally:
            chemin_temp.unlink(missing_ok=True)  # nettoyage garanti

    llm = _creer_llm(MODEL_TEXTE)
    message = HumanMessage(content=f"{PROMPT_EXTRACTION}\n\nContenu de la facture :\n{texte}")
    reponse = llm.invoke([message])
    return json.loads(_nettoyer_json(reponse.content.strip()))


def extraire_donnees_facture(chemin_fichier: str, nom_fichier: str) -> dict | None:
    """
    Point d'entrée principal — envoie la facture au LLM
    et récupère les données structurées.
    """
    try:
        path = _valider_chemin_fichier(chemin_fichier)
        extension = path.suffix.lower().lstrip(".")

        if extension in EXTENSIONS_IMAGES:
            donnees = _extraire_depuis_image(path)
        elif extension == "pdf":
            donnees = _extraire_depuis_pdf(path)
        else:
            return None

        return valider_et_enrichir(donnees, nom_fichier)

    except FileNotFoundError as e:
        logger.error("Fichier introuvable : %s", e)
        return None
    except ValueError as e:
        logger.error("Validation échouée pour %s : %s", nom_fichier, e)
        return None
    except json.JSONDecodeError as e:
        logger.error("Réponse LLM non JSON pour %s : %s", nom_fichier, e)
        return None
    except Exception as e:
        logger.error("Erreur inattendue pour %s : %s", nom_fichier, type(e).__name__)
        return None


# ==============================
# VALIDATION
# ==============================
def valider_et_enrichir(donnees: dict, nom_fichier: str) -> dict | None:
    """
    Valide les données extraites et calcule les valeurs dérivées.
    Python fait les calculs, pas le LLM.
    """
    if not donnees:
        return None

    if not donnees.get("consommation_kwh") or not donnees.get("duree_jours"):
        logger.warning("Champs obligatoires manquants dans %s", nom_fichier)
        return None

    try:
        consommation = float(donnees["consommation_kwh"])
        duree = int(donnees["duree_jours"])
        montant = float(donnees.get("montant_ttc") or 0)
        puissance = float(donnees.get("puissance_souscrite_kva") or 0)
    except (TypeError, ValueError) as e:
        logger.warning("Conversion numérique échouée pour %s : %s", nom_fichier, e)
        return None

    # Validation des plages
    if not (CONSO_MIN_KWH <= consommation <= CONSO_MAX_KWH):
        logger.warning(
            "Consommation hors plage pour %s : %s kWh", nom_fichier, consommation
        )
        return None

    if montant > 0 and not (MONTANT_MIN_FCFA <= montant <= MONTANT_MAX_FCFA):
        logger.warning(
            "Montant hors plage pour %s : %s FCFA", nom_fichier, montant
        )
        return None

    if duree <= 0 or duree > 365:
        logger.warning("Durée invalide pour %s : %s jours", nom_fichier, duree)
        return None

    conso_journaliere = round(consommation / duree, 2)
    tarif_moyen = round(montant / consommation, 2) if consommation > 0 else 0

    return {
        "nom_fichier": nom_fichier,
        "periode": str(donnees.get("periode") or ""),
        "duree_jours": duree,
        "consommation_kwh": consommation,
        "consommation_journaliere_kwh": conso_journaliere,
        "puissance_souscrite_kva": puissance,
        "montant_ttc": montant,
        "tarif_moyen": tarif_moyen,
        "fournisseur": str(donnees.get("fournisseur") or ""),
        "usage": str(donnees.get("usage") or "")
    }