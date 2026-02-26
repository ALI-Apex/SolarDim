import os
import json
import base64
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import fitz  # PyMuPDF

load_dotenv()

def image_en_base64(chemin_image: str) -> str:
    """Convertit une image en base64 pour l'envoyer au LLM"""
    with open(chemin_image, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extraire_donnees_facture(chemin_fichier: str, nom_fichier: str) -> dict | None:
    """
    Envoie la facture au LLM et récupère les données structurées.
    Fonctionne avec images (JPG, PNG) et PDF.
    Retourne un dictionnaire avec les données extraites ou None si échec.
    """

    # Détermination du type de fichier
    extension = nom_fichier.lower().split(".")[-1]

    # Modèle vision pour les images, modèle standard pour les PDF texte
    llm_vision = ChatGroq(
        model="meta-llama/llama-4-scout-17b-16e-instruct",  # modèle vision de Groq
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
    )

    llm_texte = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
    )

    prompt_extraction = """Tu es un expert en lecture de factures d'électricité.
    
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

    try:
        if extension in ["jpg", "jpeg", "png"]:
            # Traitement image
            image_b64 = image_en_base64(chemin_fichier)
            media_type = "image/jpeg" if extension in ["jpg", "jpeg"] else "image/png"

            # Groq supporte la vision avec llama
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": prompt_extraction
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_b64}"
                        }
                    }
                ]
            )
            reponse = llm_vision.invoke([message])

        elif extension == "pdf":
            # Pour les PDF on extrait d'abord le texte avec PyMuPDF
            doc = fitz.open(chemin_fichier)
            texte = ""
            for page in doc:
                texte += page.get_text()
            doc.close()

            if not texte.strip():
                # PDF scanné sans texte → on le convertit en image
                doc = fitz.open(chemin_fichier)
                page = doc[0]
                pix = page.get_pixmap(dpi=200)
                chemin_temp = chemin_fichier.replace(".pdf", "_temp.png")
                pix.save(chemin_temp)
                doc.close()
                return extraire_donnees_facture(chemin_temp, "temp.png")

            message = HumanMessage(
                content=f"{prompt_extraction}\n\nContenu de la facture :\n{texte}"
            )
            reponse = llm_texte.invoke([message])
        else:
            return None

        # Appel au LLM

        texte_reponse = reponse.content.strip()

        # Nettoyage au cas où le LLM ajoute des backticks markdown
        if "```json" in texte_reponse:
            texte_reponse = texte_reponse.split("```json")[1].split("```")[0].strip()
        elif "```" in texte_reponse:
            texte_reponse = texte_reponse.split("```")[1].split("```")[0].strip()

        donnees = json.loads(texte_reponse)
        return donnees

    except Exception as e:
        print(f"Erreur extraction facture {nom_fichier} : {e}")
        return None


def valider_et_enrichir(donnees: dict, nom_fichier: str) -> dict | None:
    """
    Valide les données extraites par le LLM et calcule
    les valeurs dérivées en Python pur.
    C'est Python qui fait les calculs, pas le LLM.
    """
    if not donnees:
        return None

    # Vérification des champs obligatoires
    if not donnees.get("consommation_kwh") or not donnees.get("duree_jours"):
        return None

    consommation = float(donnees["consommation_kwh"])
    duree = int(donnees["duree_jours"])
    montant = float(donnees.get("montant_ttc") or 0)

    # Calculs Python — pas le LLM
    conso_journaliere = round(consommation / duree, 2) if duree > 0 else 0
    tarif_moyen = round(montant / consommation, 2) if consommation > 0 else 0

    return {
        "nom_fichier": nom_fichier,
        "periode": donnees.get("periode", ""),
        "duree_jours": duree,
        "consommation_kwh": consommation,
        "consommation_journaliere_kwh": conso_journaliere,
        "puissance_souscrite_kva": float(donnees.get("puissance_souscrite_kva") or 0),
        "montant_ttc": montant,
        "tarif_moyen": tarif_moyen,
        "fournisseur": donnees.get("fournisseur", ""),
        "usage": donnees.get("usage", "")
    }