import sqlite3
import os
import logging
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

# ==============================
# CONSTANTES
# ==============================
PATH_DB = Path(os.getenv("DB_PATH", "data/pv_dimensioning.db"))


# ==============================
# CONNEXION
# ==============================
def get_connection() -> sqlite3.Connection:
    """Retourne une connexion à la base de données."""
    PATH_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PATH_DB))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """
    Context manager pour les connexions SQLite.
    Garantit la fermeture de la connexion même en cas d'exception.

    Usage :
        with get_db() as conn:
            conn.execute(...)
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==============================
# INITIALISATION
# ==============================
def initialiser_stockage() -> None:
    """Crée les tables si elles n'existent pas encore."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS equipements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                puissance_w REAL NOT NULL CHECK(puissance_w >= 0),
                heures_par_jour REAL NOT NULL CHECK(heures_par_jour >= 0 AND heures_par_jour <= 24),
                quantite INTEGER NOT NULL CHECK(quantite >= 1),
                conso_jour_wh REAL NOT NULL CHECK(conso_jour_wh >= 0),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS factures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_fichier TEXT NOT NULL,
                chemin TEXT,
                periode TEXT,
                duree_jours INTEGER CHECK(duree_jours > 0),
                consommation_kwh REAL CHECK(consommation_kwh >= 0),
                consommation_journaliere_kwh REAL CHECK(consommation_journaliere_kwh >= 0),
                puissance_souscrite_kva REAL CHECK(puissance_souscrite_kva >= 0),
                montant_ttc REAL CHECK(montant_ttc >= 0),
                tarif_moyen REAL CHECK(tarif_moyen >= 0),
                fournisseur TEXT,
                usage TEXT,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS onduleur (
                id INTEGER PRIMARY KEY DEFAULT 1,
                tension_demarrage_batterie_v REAL CHECK(tension_demarrage_batterie_v > 0),
                nb_strings INTEGER DEFAULT 1 CHECK(nb_strings IN (1, 2))
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS onduleur_strings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_string INTEGER NOT NULL CHECK(numero_string IN (1, 2)),
                voc_max_v REAL CHECK(voc_max_v > 0),
                vmppt_min_v REAL CHECK(vmppt_min_v > 0),
                vmppt_max_v REAL CHECK(vmppt_max_v > 0),
                imax_a REAL CHECK(imax_a > 0)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS module_pv (
                id INTEGER PRIMARY KEY DEFAULT 1,
                puissance_crete_wc REAL CHECK(puissance_crete_wc > 0),
                voc_v REAL CHECK(voc_v > 0),
                isc_a REAL CHECK(isc_a > 0),
                vmp_v REAL CHECK(vmp_v > 0),
                imp_a REAL CHECK(imp_a > 0),
                longueur_m REAL CHECK(longueur_m > 0),
                largeur_m REAL CHECK(largeur_m > 0),
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS batterie (
                id INTEGER PRIMARY KEY DEFAULT 1,
                tension_v REAL CHECK(tension_v > 0),
                capacite_ah REAL CHECK(capacite_ah > 0),
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS parametres (
                id INTEGER PRIMARY KEY DEFAULT 1,
                tarif_kwh REAL DEFAULT 150 CHECK(tarif_kwh >= 0),
                prix_total_installation REAL DEFAULT 0 CHECK(prix_total_installation >= 0),
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            INSERT OR IGNORE INTO parametres (id, tarif_kwh, prix_total_installation)
            VALUES (1, 150, 0)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS localisation (
                id INTEGER PRIMARY KEY DEFAULT 1,
                ville TEXT NOT NULL,
                latitude REAL NOT NULL CHECK(latitude BETWEEN -90 AND 90),
                longitude REAL NOT NULL CHECK(longitude BETWEEN -180 AND 180),
                irradiation_annuelle_kwh REAL,
                hsp_moyen REAL CHECK(hsp_moyen > 0),
                production_annuelle_kwh REAL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


# ==============================
# ÉQUIPEMENTS
# ==============================
def ajouter_equipement(
    nom: str,
    puissance_w: float,
    heures_par_jour: float,
    quantite: int,
    conso_jour_wh: float
) -> None:
    """Insère un nouvel équipement dans la base."""
    if not nom or not nom.strip():
        raise ValueError("Nom équipement invalide")
    if puissance_w < 0:
        raise ValueError("Puissance invalide")
    if not (0 <= heures_par_jour <= 24):
        raise ValueError("Heures/jour invalide")
    if quantite < 1:
        raise ValueError("Quantité invalide")

    with get_db() as conn:
        conn.execute("""
            INSERT INTO equipements (nom, puissance_w, heures_par_jour, quantite, conso_jour_wh)
            VALUES (?, ?, ?, ?, ?)
        """, (nom.strip(), puissance_w, heures_par_jour, quantite, conso_jour_wh))


def get_equipements() -> list:
    """Retourne tous les équipements."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM equipements").fetchall()
    return [dict(row) for row in rows]


def supprimer_equipement(equipement_id: int) -> None:
    """Supprime un équipement par son id."""
    with get_db() as conn:
        conn.execute("DELETE FROM equipements WHERE id = ?", (equipement_id,))


def effacer_equipements() -> None:
    """Supprime tous les équipements."""
    with get_db() as conn:
        conn.execute("DELETE FROM equipements")


# ==============================
# FACTURES
# ==============================
def sauvegarder_facture(donnees: dict) -> None:
    """Sauvegarde les données extraites d'une facture."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO factures (
                nom_fichier, chemin, periode, duree_jours,
                consommation_kwh, consommation_journaliere_kwh,
                puissance_souscrite_kva, montant_ttc,
                tarif_moyen, fournisseur, usage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            donnees.get("nom_fichier", ""),
            donnees.get("chemin", ""),
            donnees.get("periode", ""),
            donnees.get("duree_jours", 0),
            donnees.get("consommation_kwh", 0),
            donnees.get("consommation_journaliere_kwh", 0),
            donnees.get("puissance_souscrite_kva", 0),
            donnees.get("montant_ttc", 0),
            donnees.get("tarif_moyen", 0),
            donnees.get("fournisseur", ""),
            donnees.get("usage", "")
        ))


def get_factures() -> list:
    """Retourne toutes les factures extraites."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM factures").fetchall()
    return [dict(row) for row in rows]


def get_consommation_moyenne() -> dict | None:
    """Calcule la consommation journalière moyenne sur toutes les factures."""
    with get_db() as conn:
        row = conn.execute("""
            SELECT AVG(consommation_journaliere_kwh) as conso_moy,
                   AVG(tarif_moyen) as tarif_moy,
                   COUNT(*) as nb_factures
            FROM factures
            WHERE consommation_journaliere_kwh > 0
        """).fetchone()

    if row and row["nb_factures"] > 0:
        return {
            "consommation_journaliere_moyenne_kwh": round(row["conso_moy"], 2),
            "tarif_moyen_fcfa_kwh": round(row["tarif_moy"], 2),
            "nombre_factures": row["nb_factures"]
        }
    return None


def effacer_factures() -> None:
    """Supprime toutes les factures."""
    with get_db() as conn:
        conn.execute("DELETE FROM factures")


# ==============================
# ONDULEUR
# ==============================
def sauvegarder_onduleur(
    tension_demarrage_batterie_v: float,
    nb_strings: int
) -> None:
    """Sauvegarde les informations générales de l'onduleur."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO onduleur (id, tension_demarrage_batterie_v, nb_strings)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                tension_demarrage_batterie_v = excluded.tension_demarrage_batterie_v,
                nb_strings = excluded.nb_strings
        """, (tension_demarrage_batterie_v, nb_strings))


def get_onduleur() -> dict | None:
    """Retourne les données de l'onduleur."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM onduleur WHERE id = 1").fetchone()
    return dict(row) if row else None


def sauvegarder_strings(
    numero_string: int,
    voc_max_v: float,
    vmppt_min_v: float,
    vmppt_max_v: float,
    imax_a: float
) -> None:
    """Sauvegarde les caractéristiques d'une entrée PV."""
    if numero_string not in (1, 2):
        raise ValueError(f"Numéro de string invalide : {numero_string}")

    with get_db() as conn:
        conn.execute(
            "DELETE FROM onduleur_strings WHERE numero_string = ?",
            (numero_string,)
        )
        conn.execute("""
            INSERT INTO onduleur_strings (numero_string, voc_max_v, vmppt_min_v, vmppt_max_v, imax_a)
            VALUES (?, ?, ?, ?, ?)
        """, (numero_string, voc_max_v, vmppt_min_v, vmppt_max_v, imax_a))


def get_strings() -> list:
    """Retourne toutes les entrées PV de l'onduleur."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM onduleur_strings ORDER BY numero_string"
        ).fetchall()
    return [dict(r) for r in rows]


def effacer_onduleur() -> None:
    """Supprime les données de l'onduleur et ses strings."""
    with get_db() as conn:
        conn.execute("DELETE FROM onduleur")
        conn.execute("DELETE FROM onduleur_strings")


# ==============================
# MODULE PV
# ==============================
def sauvegarder_module_pv(
    puissance_crete_wc: float,
    voc_v: float,
    isc_a: float,
    vmp_v: float,
    imp_a: float,
    longueur_m: float,
    largeur_m: float
) -> None:
    """Sauvegarde les caractéristiques du module PV."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO module_pv (id, puissance_crete_wc, voc_v, isc_a, vmp_v, imp_a, longueur_m, largeur_m)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                puissance_crete_wc = excluded.puissance_crete_wc,
                voc_v = excluded.voc_v,
                isc_a = excluded.isc_a,
                vmp_v = excluded.vmp_v,
                imp_a = excluded.imp_a,
                longueur_m = excluded.longueur_m,
                largeur_m = excluded.largeur_m,
                updated_at = CURRENT_TIMESTAMP
        """, (puissance_crete_wc, voc_v, isc_a, vmp_v, imp_a, longueur_m, largeur_m))


def get_module_pv() -> dict | None:
    """Retourne les données du module PV."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM module_pv WHERE id = 1").fetchone()
    return dict(row) if row else None


def effacer_module_pv() -> None:
    """Supprime les données du module PV."""
    with get_db() as conn:
        conn.execute("DELETE FROM module_pv")


# ==============================
# BATTERIE
# ==============================
def sauvegarder_batterie(tension_v: float, capacite_ah: float) -> None:
    """Sauvegarde les caractéristiques de la batterie unitaire."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO batterie (id, tension_v, capacite_ah)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                tension_v = excluded.tension_v,
                capacite_ah = excluded.capacite_ah,
                updated_at = CURRENT_TIMESTAMP
        """, (tension_v, capacite_ah))


def get_batterie() -> dict | None:
    """Retourne les données de la batterie."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM batterie WHERE id = 1").fetchone()
    return dict(row) if row else None


def effacer_batterie() -> None:
    """Supprime les données de la batterie."""
    with get_db() as conn:
        conn.execute("DELETE FROM batterie")


# ==============================
# COMPOSANTS (helper)
# ==============================
def get_composants() -> dict:
    """Retourne un résumé de tous les composants disponibles."""
    return {
        "onduleur": get_onduleur(),
        "module_pv": get_module_pv(),
        "batterie": get_batterie()
    }


# ==============================
# PARAMÈTRES
# ==============================
def get_parametres() -> dict:
    """Retourne les paramètres économiques."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM parametres WHERE id = 1").fetchone()
    return dict(row) if row else {"tarif_kwh": 150, "prix_total_installation": 0}


def sauvegarder_parametres(
    tarif_kwh: float,
    prix_total_installation: float
) -> None:
    """Sauvegarde les paramètres économiques."""
    if tarif_kwh < 0:
        raise ValueError("Tarif kWh invalide")
    if prix_total_installation < 0:
        raise ValueError("Prix installation invalide")

    with get_db() as conn:
        conn.execute("""
            INSERT INTO parametres (id, tarif_kwh, prix_total_installation)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                tarif_kwh = excluded.tarif_kwh,
                prix_total_installation = excluded.prix_total_installation,
                updated_at = CURRENT_TIMESTAMP
        """, (tarif_kwh, prix_total_installation))


# ==============================
# LOCALISATION
# ==============================
def sauvegarder_localisation(
    ville: str,
    latitude: float,
    longitude: float,
    irradiation_annuelle: float,
    hsp_moyen: float,
    production_annuelle: float
) -> None:
    """Sauvegarde les données de localisation et d'ensoleillement."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO localisation (
                id, ville, latitude, longitude,
                irradiation_annuelle_kwh, hsp_moyen, production_annuelle_kwh
            )
            VALUES (1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                ville = excluded.ville,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                irradiation_annuelle_kwh = excluded.irradiation_annuelle_kwh,
                hsp_moyen = excluded.hsp_moyen,
                production_annuelle_kwh = excluded.production_annuelle_kwh,
                updated_at = CURRENT_TIMESTAMP
        """, (ville, latitude, longitude, irradiation_annuelle, hsp_moyen, production_annuelle))


def get_localisation() -> dict | None:
    """Retourne les données de localisation."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM localisation WHERE id = 1").fetchone()
    return dict(row) if row else None