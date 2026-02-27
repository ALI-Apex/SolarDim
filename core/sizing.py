import math
import logging

logger = logging.getLogger(__name__)

# ==============================
# CONSTANTES
# ==============================
PERFORMANCE_RATIO_DEFAULT = 0.65
PUISSANCE_PANNEAU_DEFAULT_WC = 500
TENSION_BATTERIE_DEFAULT_V = 48
PROFONDEUR_DECHARGE_DEFAULT = 0.95
AUTONOMIE_DEFAULT_JOURS = 1
COEFFICIENT_AERATION_DEFAULT = 1.1
HSP_MIN = 0.1
HSP_MAX = 12.0


# ==============================
# CALCULS DE BASE
# ==============================

def calculer_consommation_journaliere(equipements: list) -> float:
    """Calcule la consommation journalière totale en Wh depuis les équipements."""
    if not equipements:
        return 0.0
    return sum(float(e["conso_jour_wh"]) for e in equipements)


def calculer_puissance_total_equipement(equipements: list) -> float:
    """Calcule la puissance totale des équipements pour dimensionner l'onduleur."""
    if not equipements:
        return 0.0
    return sum(float(e["puissance_w"]) * int(e.get("quantite", 1)) for e in equipements)


def calculer_puissance_crete(
    conso_journaliere_wh: float,
    hsp: float,
    performance_ratio: float = PERFORMANCE_RATIO_DEFAULT
) -> float:
    """
    Calcule la puissance crête nécessaire en Wc.
    P_crete = Consommation_journalière / (HSP × PR)
    """
    if hsp <= 0 or hsp > HSP_MAX:
        raise ValueError(f"HSP invalide : {hsp} (attendu entre 0 et {HSP_MAX})")
    if conso_journaliere_wh < 0:
        raise ValueError(f"Consommation invalide : {conso_journaliere_wh}")
    if not (0 < performance_ratio <= 1):
        raise ValueError(f"Performance Ratio invalide : {performance_ratio}")

    return round(conso_journaliere_wh / (hsp * performance_ratio), 2)


def calculer_nombre_panneaux(
    puissance_crete_wc: float,
    puissance_panneau_wc: float
) -> int:
    """Calcule le nombre de panneaux — arrondi au supérieur."""
    if puissance_panneau_wc <= 0:
        logger.warning("Puissance panneau invalide : %s Wc", puissance_panneau_wc)
        return 0
    if puissance_crete_wc <= 0:
        return 0
    return math.ceil(puissance_crete_wc / puissance_panneau_wc)


# ==============================
# CONFIGURATION STRINGS
# ==============================

def calculer_configuration_strings(
    nb_panneaux: int,
    module: dict,
    strings: list
) -> dict | None:
    """
    Calcule la configuration série/parallèle pour chaque string.
    Nécessite : Voc, Vmp, Imp du module + données des strings.
    Retourne None si données insuffisantes.
    """
    if not strings or not module:
        return None

    voc = float(module["voc_v"]) if module.get("voc_v") is not None else None
    vmp = float(module["vmp_v"]) if module.get("vmp_v") is not None else None
    imp = float(module["imp_a"]) if module.get("imp_a") is not None else None

    if not voc or not vmp:
        return None

    resultats_strings = []
    panneaux_restants = nb_panneaux
    avertissements = []

    for s in strings:
        voc_max = float(s["voc_max_v"]) if s.get("voc_max_v") is not None else None
        vmppt_min = float(s["vmppt_min_v"]) if s.get("vmppt_min_v") is not None else None
        vmppt_max = float(s["vmppt_max_v"]) if s.get("vmppt_max_v") is not None else None
        imax = float(s["imax_a"]) if s.get("imax_a") is not None else None

        string_result = {"numero_string": s["numero_string"]}

        # --- Calcul série ---
        nb_serie_min = None
        nb_serie_max_mppt = None  # ← correction du bug
        nb_serie_max_absolu = None

        if vmppt_min and vmp:
            nb_serie_min = math.ceil(vmppt_min / vmp)
            string_result["nb_serie_min"] = nb_serie_min

        if vmppt_max and vmp:
            nb_serie_max_mppt = math.floor(vmppt_max / vmp)  # ← floor, pas ceil
            string_result["nb_serie_max_mppt"] = nb_serie_max_mppt

        if voc_max and voc:
            nb_serie_max_absolu = math.floor(voc_max / voc)
            string_result["nb_serie_max_absolu"] = nb_serie_max_absolu

        # Nb série optimal = max MPPT si disponible, sinon max absolu
        nb_serie_optimal = nb_serie_max_mppt or nb_serie_max_absolu
        if not nb_serie_optimal:
            logger.warning("String %s ignorée — données insuffisantes", s["numero_string"])
            continue

        string_result["nb_serie_optimal"] = nb_serie_optimal

        # Vérification sécurité Voc
        if nb_serie_max_absolu and nb_serie_optimal > nb_serie_max_absolu:
            nb_serie_optimal = nb_serie_max_absolu
            avertissements.append(
                f"⚠️ String {s['numero_string']} : nb série réduit à {nb_serie_max_absolu} "
                f"pour respecter Voc max ({voc_max}V)"
            )

        # Vérification plancher MPPT
        if nb_serie_min and nb_serie_optimal < nb_serie_min:
            avertissements.append(
                f"⚠️ String {s['numero_string']} : tension MPPT insuffisante — "
                f"min {nb_serie_min} panneaux en série requis"
            )

        # --- Calcul parallèle ---
        nb_parallele_max = None
        if imax and imp:
            nb_parallele_max = math.floor(imax / imp)
            string_result["nb_parallele_max"] = nb_parallele_max

        # Dispatch des panneaux
        if panneaux_restants <= 0:
            string_result.update({
                "nb_serie_affecte": 0,
                "nb_parallele_affecte": 0,
                "nb_panneaux_affectes": 0
            })
        else:
            cap_parallele = nb_parallele_max if nb_parallele_max else 1
            nb_max_string = nb_serie_optimal * cap_parallele
            nb_affectes = min(panneaux_restants, nb_max_string)
            nb_parallele_reel = math.ceil(nb_affectes / nb_serie_optimal)

            string_result.update({
                "nb_serie_affecte": nb_serie_optimal,
                "nb_parallele_affecte": nb_parallele_reel,
                "nb_panneaux_affectes": nb_serie_optimal * nb_parallele_reel,
                "tension_string_v": round(nb_serie_optimal * vmp, 2)
            })
            panneaux_restants -= string_result["nb_panneaux_affectes"]

        resultats_strings.append(string_result)

    if panneaux_restants > 0:
        avertissements.append(
            f"⚠️ {panneaux_restants} panneau(x) non affecté(s) — "
            f"capacité des strings insuffisante"
        )

    return {
        "strings": resultats_strings,
        "avertissements": avertissements,
        "panneaux_non_affectes": panneaux_restants
    }


# ==============================
# SURFACE DU CHAMP PV
# ==============================

def calculer_surface_champ(
    nb_panneaux: int,
    module: dict,
    coefficient_aeration: float = COEFFICIENT_AERATION_DEFAULT
) -> dict | None:
    """
    Calcule la surface totale du champ PV.
    Coefficient d'aération de 1.1 appliqué.
    """
    longueur = float(module["longueur_m"]) if module and module.get("longueur_m") is not None else None
    largeur = float(module["largeur_m"]) if module and module.get("largeur_m") is not None else None

    if not longueur or not largeur:
        return None

    surface_module = longueur * largeur
    surface_brute = nb_panneaux * surface_module
    surface_totale = round(surface_brute * coefficient_aeration, 2)

    return {
        "surface_module_m2": round(surface_module, 3),
        "surface_brute_m2": round(surface_brute, 2),
        "surface_totale_m2": surface_totale,
        "coefficient_aeration": coefficient_aeration
    }


# ==============================
# BATTERIE
# ==============================

def calculer_batterie(
    conso_journaliere_wh: float,
    autonomie_jours: float = AUTONOMIE_DEFAULT_JOURS,
    tension_batterie_v: float = TENSION_BATTERIE_DEFAULT_V,
    profondeur_decharge: float = PROFONDEUR_DECHARGE_DEFAULT
) -> dict:
    """
    Calcule la capacité de batterie nécessaire.
    Formule : C = (Conso × Autonomie) / (Tension × DoD)
    """
    conso_journaliere_wh = float(conso_journaliere_wh)
    tension_batterie_v = float(tension_batterie_v)
    autonomie_jours = float(autonomie_jours)
    profondeur_decharge = float(profondeur_decharge)

    if tension_batterie_v <= 0:
        raise ValueError(f"Tension batterie invalide : {tension_batterie_v}")
    if not (0 < profondeur_decharge <= 1):
        raise ValueError(f"Profondeur de décharge invalide : {profondeur_decharge}")

    capacite_ah = (conso_journaliere_wh * autonomie_jours) / (tension_batterie_v * profondeur_decharge)
    capacite_kwh = (conso_journaliere_wh * autonomie_jours) / 1000

    return {
        "capacite_ah": round(capacite_ah, 2),
        "capacite_kwh": round(capacite_kwh, 2),
        "tension_v": tension_batterie_v,
        "autonomie_jours": autonomie_jours,
        "profondeur_decharge": profondeur_decharge
    }


def calculer_configuration_batterie(
    batterie_necessaire: dict,
    batterie_unitaire: dict,
    onduleur: dict = None
) -> dict | None:
    """
    Calcule la configuration série/parallèle du parc batterie.
    """
    if not batterie_unitaire:
        return None

    tension_unitaire = float(batterie_unitaire["tension_v"]) if batterie_unitaire.get("tension_v") is not None else None
    capacite_unitaire = float(batterie_unitaire["capacite_ah"]) if batterie_unitaire.get("capacite_ah") is not None else None

    if not tension_unitaire or not capacite_unitaire:
        return None

    tension_systeme = float(batterie_necessaire["tension_v"])
    capacite_totale = float(batterie_necessaire["capacite_ah"])

    nb_serie = math.ceil(tension_systeme / tension_unitaire)
    nb_parallele = math.ceil(capacite_totale / capacite_unitaire)

    avertissement_tension = None
    if onduleur and onduleur.get("tension_demarrage_batterie_v"):
        tension_reelle = nb_serie * tension_unitaire
        tension_demarrage = float(onduleur["tension_demarrage_batterie_v"])
        if tension_reelle < tension_demarrage:
            avertissement_tension = (
                f"⚠️ Tension parc batterie ({tension_reelle}V) "
                f"inférieure à la tension de démarrage onduleur ({tension_demarrage}V)"
            )

    return {
        "nb_batteries_serie": nb_serie,
        "nb_batteries_parallele": nb_parallele,
        "nb_batteries_total": nb_serie * nb_parallele,
        "tension_parc_v": round(nb_serie * tension_unitaire, 2),
        "capacite_reelle_ah": round(nb_parallele * capacite_unitaire, 2),
        "avertissement_tension": avertissement_tension
    }


# ==============================
# RENTABILITÉ
# ==============================

def calculer_rentabilite(
    prix_total_installation: float,
    production_annuelle_kwh: float,
    tarif_kwh: float = 150,
) -> dict:
    """
    Calcule l'étude de rentabilité sur 10 ans.
    """
    if prix_total_installation < 0:
        raise ValueError("Prix installation invalide")
    if production_annuelle_kwh <= 0:
        raise ValueError("Production annuelle invalide")
    if tarif_kwh <= 0:
        raise ValueError("Tarif kWh invalide")

    economies_annuelles = production_annuelle_kwh * tarif_kwh
    temps_retour = round(prix_total_installation / economies_annuelles, 1) if economies_annuelles > 0 else 0

    projection = []
    cumul = -prix_total_installation
    for annee in range(1, 11):
        cumul += economies_annuelles
        projection.append({
            "annee": annee,
            "economies_cumulees": round(cumul, 2)
        })

    return {
        "cout_total_installation": round(prix_total_installation, 2),
        "economies_annuelles": round(economies_annuelles, 2),
        "temps_retour_ans": temps_retour,
        "projection_10_ans": projection
    }


# ==============================
# DIMENSIONNEMENT COMPLET
# ==============================

def calculer_dimensionnement_complet(
    hsp: float,
    equipements: list = None,
    conso_journaliere_kwh: float = None,
    puissance_panneau_wc: float = PUISSANCE_PANNEAU_DEFAULT_WC,
    tension_batterie_v: float = TENSION_BATTERIE_DEFAULT_V,
    module: dict = None,
    onduleur: dict = None,
    strings: list = None,
    batterie_unitaire: dict = None
) -> dict:
    """
    Orchestre tous les calculs de dimensionnement.

    Deux modes :
    - Mode équipements : equipements est une liste d'appareils
    - Mode factures    : conso_journaliere_kwh est la moyenne des factures
    """
    hsp = float(hsp)
    if not (HSP_MIN <= hsp <= HSP_MAX):
        raise ValueError(f"HSP invalide : {hsp}")

    # --- Consommation journalière ---
    if equipements:
        conso_j_wh = calculer_consommation_journaliere(equipements)
        puissance_totale_w = calculer_puissance_total_equipement(equipements)
        source_conso = "equipements"
    elif conso_journaliere_kwh:
        conso_j_wh = float(conso_journaliere_kwh) * 1000
        puissance_totale_w = (conso_j_wh / 8) * 1.25
        source_conso = "factures"
    else:
        raise ValueError("Fournissez soit les équipements soit la consommation journalière.")

    # --- Puissance panneau ---
    if module and module.get("puissance_crete_wc"):
        puissance_panneau_wc = float(module["puissance_crete_wc"])

    # --- Tension système ---
    if onduleur and onduleur.get("tension_demarrage_batterie_v"):
        tension_batterie_v = float(onduleur["tension_demarrage_batterie_v"])
    elif batterie_unitaire and batterie_unitaire.get("tension_v"):
        tension_batterie_v = float(batterie_unitaire["tension_v"])

    # --- Calculs de base ---
    puissance_crete = calculer_puissance_crete(conso_j_wh, hsp)
    nb_panneaux = calculer_nombre_panneaux(puissance_crete, puissance_panneau_wc)
    puissance_installee = nb_panneaux * puissance_panneau_wc
    batterie = calculer_batterie(conso_j_wh, tension_batterie_v=tension_batterie_v)
    puissance_onduleur_w = puissance_totale_w * 1.25

    result = {
        "source_consommation": source_conso,
        "consommation_journaliere_wh": round(conso_j_wh, 2),
        "consommation_journaliere_kwh": round(conso_j_wh / 1000, 2),
        "puissance_crete_necessaire_wc": puissance_crete,
        "puissance_panneau_wc": puissance_panneau_wc,
        "nombre_panneaux": nb_panneaux,
        "puissance_installee_wc": puissance_installee,
        "puissance_installee_kwc": round(puissance_installee / 1000, 2),
        "batterie": batterie,
        "puissance_onduleur_recommandee_w": round(puissance_onduleur_w, 2),
        "puissance_onduleur_recommandee_kva": round(puissance_onduleur_w / 1000, 2),
        "hsp_utilise": hsp,
        "configuration_strings": None,
        "surface_champ": None,
        "configuration_batterie": None,
    }

    # --- Calculs enrichis ---
    if module and strings:
        result["configuration_strings"] = calculer_configuration_strings(
            nb_panneaux, module, strings
        )

    if module and module.get("longueur_m") and module.get("largeur_m"):
        result["surface_champ"] = calculer_surface_champ(nb_panneaux, module)

    if batterie_unitaire:
        result["configuration_batterie"] = calculer_configuration_batterie(
            batterie, batterie_unitaire, onduleur
        )

    return result