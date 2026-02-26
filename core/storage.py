import sqlite3
import os
from datetime import datetime

PATH_DB = "data/pv_dimensioning.db"

def get_connection():
    """Retourne une connexion à la base de donnee """
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(PATH_DB)
    conn.row_factory = sqlite3.Row #Permet aux colonnes par leurs noms
    return conn



def initialiser_stockage():
    """Créer les tables si elles n'existe pas encore"""
    conn = get_connection()
    cursor = conn.cursor()

    # ============ TABLE equipement =================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom  TEXT NOT NULL,
            puissance_w REAL NOT NULL,
            heures_par_jour REAL NOT NULL,
            quantite INTEGER NOT NULL,
            conso_jour_wh REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ================ TABLE factures ======================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS factures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_fichier TEXT NOT NULL,
            chemin TEXT,
            periode TEXT,
            duree_jours INTEGER,
            consommation_kwh REAL,
            consommation_journaliere_kwh REAL,
            puissance_souscrite_kva REAL,
            montant_ttc REAL,
            tarif_moyen REAL,
            fournisseur TEXT,
            usage TEXT,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ============= TABLE Configurations ================
    # ----  table onduleur ----
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS onduleur (
            id INTEGER PRIMARY KEY DEFAULT 1,
            tension_demarrage_batterie_v REAL,
            nb_strings INTEGER DEFAULT 1
        )
    """)

    # ----- table onduleur_strings ----
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS onduleur_strings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_string INTEGER NOT NULL,
            voc_max_v REAL,
            vmppt_min_v REAL,
            vmppt_max_v REAL,
            imax_a REAL
        )
    """)


    # ----- table module_pv ------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS module_pv (
            id INTEGER PRIMARY KEY DEFAULT 1,
            puissance_crete_wc REAL,
            voc_v REAL,
            isc_a REAL,
            vmp_v REAL,
            imp_a REAL,
            longueur_m REAL,
            largeur_m REAL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---- table batterie --------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batterie (
            id INTEGER PRIMARY KEY DEFAULT 1,
            tension_v REAL,
            capacite_ah REAL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ------ Table paramètres ------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parametres (
            id INTEGER PRIMARY KEY DEFAULT 1, 
            tarif_kwh REAL DEFAULT 150,
            prix_total_installation REAL DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insertion des valeurs par défaut si la table est vide
    cursor.execute("""
        INSERT OR IGNORE INTO parametres (id, tarif_kwh, prix_total_installation)
        VALUES (1, 150, 0)
    """)

    # ============= TABLE localisation =======================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS localisation (
            id INTEGER PRIMARY KEY DEFAULT 1,
            ville TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            irradiation_annuelle_kwh REAL,
            hsp_moyen REAL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# ================== Fonctions pour les équipements =====================

def ajouter_equipement(nom, puissance_w, heures_par_jour, quantite, conso_jour_wh):
    """Insère un nouvel équipement dans la base"""
    conn = get_connection()
    conn.execute("""
        INSERT INTO equipements (nom, puissance_w, heures_par_jour, quantite, conso_jour_wh)
        VALUES (?, ?, ?, ?, ?)
    """, (nom, puissance_w, heures_par_jour, quantite, conso_jour_wh))
    conn.commit()
    conn.close()

def get_equipements():
    """Retourne tous les équipements sous forme de liste de dictionnaires"""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM equipements").fetchall()
    conn.close()
    # On convertit chaque Row en dictionnaire Python classique
    return [dict(row) for row in rows]

def supprimer_equipement(equipement_id):
    """Supprime un équipement par son id"""
    conn = get_connection()
    conn.execute("DELETE FROM equipements WHERE id = ?", (equipement_id,))
    conn.commit()
    conn.close()

def effacer_equipements():
    """Supprime tous les équipements"""
    conn = get_connection()
    conn.execute("DELETE FROM equipements")
    conn.commit()
    conn.close()


# ===================== Fonction pour les  Factures ======================

def sauvegarder_facture(donnees: dict):
    """Sauvegarde les données extraites d'une facture"""
    conn = get_connection()
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
    conn.commit()
    conn.close()

def get_factures():
    """Retourne toutes les factures extraites"""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM factures").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_consommation_moyenne() -> dict | None:
    """
    Calcule la consommation journalière moyenne
    sur toutes les factures disponibles.
    C'est cette valeur qu'on passera à l'agent.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT AVG(consommation_journaliere_kwh) as conso_moy,
               AVG(tarif_moyen) as tarif_moy,
               COUNT(*) as nb_factures
        FROM factures
    """).fetchone()
    conn.close()

    if rows and rows["nb_factures"] > 0:
        return {
            "consommation_journaliere_moyenne_kwh": round(rows["conso_moy"], 2),
            "tarif_moyen_fcfa_kwh": round(rows["tarif_moy"], 2),
            "nombre_factures": rows["nb_factures"]
        }
    return None

def effacer_factures():
    conn = get_connection()
    conn.execute("DELETE Configuration batterieE FROM factures")
    conn.commit()
    conn.close()


# ================== Fonctions pour les composants =====================

# ---- Onduleur ----
def sauvegarder_onduleur(tension_demarrage_batterie_v: float, nb_strings: int):
    conn = get_connection()
    conn.execute("""
        INSERT INTO onduleur (id, tension_demarrage_batterie_v, nb_strings)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            tension_demarrage_batterie_v = excluded.tension_demarrage_batterie_v,
            nb_strings = excluded.nb_strings
    """, ( tension_demarrage_batterie_v, nb_strings))
    conn.commit()
    conn.close()

def get_onduleur():
    conn = get_connection()
    row = conn.execute("SELECT * FROM onduleur WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None

def sauvegarder_strings(numero_string: int, voc_max_v: float,
                        vmppt_min_v: float,vmppt_max_v: float,
                        imax_a: float):
    conn = get_connection()
    # Un seul enregistrement par numéro de string
    conn.execute("DELETE FROM onduleur_strings WHERE numero_string = ?", (numero_string,))
    conn.execute("""
        INSERT INTO onduleur_strings (numero_string, voc_max_v, vmppt_min_v, vmppt_max_v, imax_a)
        VALUES (?, ?, ?, ?, ?)
    """, (numero_string, voc_max_v, vmppt_min_v, vmppt_max_v, imax_a))
    conn.commit()
    conn.close()

def get_strings() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM onduleur_strings ORDER BY numero_string"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def effacer_onduleur():
    conn = get_connection()
    conn.execute("DELETE FROM onduleur")
    conn.execute("DELETE FROM onduleur_strings")
    conn.commit()
    conn.close()

# ---- Module PV -----
def sauvegarder_module_pv(puissance_crete_wc, voc_v, isc_a, vmp_v, imp_a, longueur_m, largeur_m):
    conn = get_connection()
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
            largeur_m = excluded.largeur_m
    """, (puissance_crete_wc, voc_v, isc_a, vmp_v, imp_a, longueur_m, largeur_m))
    conn.commit()
    conn.close()

def get_module_pv():
    conn = get_connection()
    row = conn.execute("SELECT * FROM module_pv WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None

def effacer_module_pv():
    conn = get_connection()
    conn.execute("DELETE FROM module_pv")
    conn.commit()
    conn.close()


# ---- Batterie -----
def sauvegarder_batterie(tension_v, capacite_ah):
    conn = get_connection()
    conn.execute("""
        INSERT INTO batterie (id, tension_v, capacite_ah)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            tension_v = excluded.tension_v,
            capacite_ah = excluded.capacite_ah
    """, (tension_v, capacite_ah))
    conn.commit()
    conn.close()

def get_batterie():
    conn = get_connection()
    row = conn.execute("SELECT * FROM batterie WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None

def effacer_batterie():
    conn = get_connection()
    conn.execute("DELETE FROM batterie")
    conn.commit()
    conn.close()

# --- Helpers pour l'agent ---

def get_composants():
    """
    Retourne un résumé de tous les composants disponibles.
    Utilisé par l'agent pour construire son contexte.
    """
    return {
        "onduleur": get_onduleur(),
        "module_pv": get_module_pv(),
        "batterie": get_batterie()
    }

# ================== Fonction pour les paramètres =======================
def get_parametres() -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM parametres WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {"tarif_kwh": 150, "prix_total_installation": 0}

def sauvegarder_parametres(tarif_kwh: float, prix_total_installation: float):
    conn = get_connection()
    conn.execute("""
        INSERT INTO parametres (id, tarif_kwh, prix_total_installation)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            tarif_kwh = excluded.tarif_kwh,
            prix_total_installation = excluded.prix_total_installation,
            updated_at = CURRENT_TIMESTAMP      
    """, (tarif_kwh, prix_total_installation))
    conn.commit()
    conn.close()


# ================= Fonctions pour la localisation =======================
def sauvegarder_localisation(ville, latitude, longitude, irradiation_annuelle, hsp_moyen, production_annuelle):
    conn = get_connection()
    conn.execute("""
        INSERT INTO localisation (id, ville, latitude, longitude, irradiation_annuelle_kwh, hsp_moyen)
        VALUES (1, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            ville = excluded.ville,
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            irradiation_annuelle_kwh = excluded.irradiation_annuelle_kwh,
            hsp_moyen = excluded.hsp_moyen,
            updated_at = CURRENT_TIMESTAMP
    """, (ville, latitude, longitude, irradiation_annuelle, hsp_moyen))
    conn.commit()
    conn.close()

def get_localisation():
    conn = get_connection()
    row = conn.execute("SELECT * FROM localisation WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None