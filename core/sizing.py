import  math


# ==============================
# CALCULS DE BASE
# ==============================

def calculer_consommation_journaliere(equipements: list) -> float:
    """Calcule la consommation journalière totale en Wh depuis les équipements"""
    return sum(float(e["conso_jour_wh"]) for e in equipements)

def calculer_puissance_total_equipement(equipements: list) -> float:
    """
    Calcule la puissance totale des équipements.
    Utilisée pour dimensionner l'onduleur.
    """
    return sum(float(e["puissance_w"]) * int(e.get("quantite", 1)) for e in equipements)

def calculer_puissance_crete(
    conso_journaliere_wh: float,
    hsp: float,
    performance_ratio: float = 0.65
) -> float:
    """
    Calcule la puissance crête nécessaire en Wc.
    P_crete = Consommation_journalière / (HSP × PR)
    PR = 0.65 pour un système off-grid
    """
    if hsp <= 0:
        raise ValueError("HSP doit être supérieur à 0")
    return round(conso_journaliere_wh / (hsp * performance_ratio), 2)

def calculer_nombre_panneaux(puissance_crete_wc: float, puissance_panneau_wc: float) -> int:
    """Calcule le nombre de panneaux — arrondi au supérieur"""
    if puissance_panneau_wc <= 0:
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

    voc = float(module.get("voc_v")) if module and module.get("voc_v") is not None else None
    vmp = float(module.get("vmp_v")) if module and module.get("vmp_v") is not None else None
    imp = float(module.get("imp_a")) if module and module.get("imp_a") is not None else None

    # On a besoin d'au moins Voc et Vmp pour calculer
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

        # ----- Calcul série -----
        nb_serie_min = None
        nb_serie_max_mppt = None
        nb_serie_max_absolu = None

        if vmppt_min and vmp:
            nb_serie_min = math.ceil(vmppt_min / vmp)
            string_result["nb_serie_min"] = nb_serie_min

        if vmppt_max and vmp:
            nb_serie_max = math.ceil(vmppt_max / vmp)
            string_result["nb_serie_max"] = nb_serie_max

        if voc_max and voc:
            nb_serie_max_absolu = math.floor(voc_max / voc)
            string_result["nb_serie_max_absolu"] = nb_serie_max_absolu

        # Nb série optimal = max MPPT si disponible, sinon max absolu
        nb_serie_optimal = nb_serie_max_mppt or nb_serie_max_absolu
        if not nb_serie_optimal:
            continue

        string_result["nb_serie_optimal"] = nb_serie_optimal

        # Vérification sécurité : nb_serie_optimal ne doit pas dépasser max absolu
        if nb_serie_max_absolu and nb_serie_optimal > nb_serie_max_absolu:
            nb_serie_optimal = nb_serie_max_absolu
            avertissements.append(
                f"⚠️ String {s['numero_string']} : nb série réduit à {nb_serie_max_absolu} "
                f"pour respecter Voc max ({voc_max}V)"
            )

        # Vérification : nb_serie_optimal >= nb_serie_min
        if nb_serie_min and nb_serie_optimal < nb_serie_min:
            avertissements.append(
                f"⚠️ String {s['numero_string']} : tension MPPT insuffisante — "
                f"min {nb_serie_min} panneaux en série requis"
            )

        # ---- Calcul parallèle ----
        nb_parallele_max = None

        if imax and imp:
            nb_parallele_max = math.floor(imax / imp)
            string_result["nb_parallele_max"] = nb_parallele_max

        # Dispatch des panneaux sur cette string
        if panneaux_restants <= 0:
            string_result["nb_serie_affecte"] = 0
            string_result["nb_parallele_affecte"] = 0
            string_result["nb_panneaux_affecte"] = 0
        else:
            # Nombre de panneaux max pour cette Entree
            cap_parallele = nb_parallele_max if nb_parallele_max else 1
            nb_max_string = nb_serie_optimal * cap_parallele

            # On affecte ce qu'on peut sans dépasser la capacité de la string
            nb_affectes = min(panneaux_restants, nb_max_string)

            # On recalcule le nb parallèle réel
            nb_parallele_reel = math.ceil(nb_affectes / nb_serie_optimal)

            string_result["nb_serie_affecte"] = nb_serie_optimal
            string_result["nb_parallele_affecte"] = nb_parallele_reel
            string_result["nb_panneaux_affectes"] = nb_serie_optimal * nb_parallele_reel
            string_result["tension_string_v"] = round(nb_serie_optimal * vmp, 2)

            panneaux_restants -= string_result["nb_panneaux_affectes"]

        resultats_strings.append(string_result)

    # Avertissement si panneaux non affectés
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
    coefficient_aeration: float = 1.1
) -> dict | None:
    """
    Calcule la surface totale du champ PV.
    Nécessite les dimensions du module.
    Coefficient d'aération de 1.1 appliqué.
    """
    longueur = float(module.get("longueur_m")) if module and module.get("longueur_m") is not None else None
    largeur = float(module.get("largeur_m")) if module and module.get("largeur_m") is not None else None

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
    autonomie_jours: float = 1,
    tension_batterie_v: float = 48,
    profondeur_decharge: float = 0.95
) -> dict:
    """
    Calcule la capacité de batterie nécessaire.
    - autonomie_jours     : 1 jour par défaut
    - tension_batterie_v  : 48V par défaut
    - profondeur_decharge : 0.95 pour lithium, 0.5 pour plomb-acide
    Formule : C = (Conso × Autonomie) / (Tension × DoD)
    """

    # Conversion forcée
    conso_journaliere_wh = float(conso_journaliere_wh)
    tension_batterie_v = float(tension_batterie_v)
    autonomie_jours = float(autonomie_jours)
    profondeur_decharge = float(profondeur_decharge)

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
    Nécessite tension et capacité de la batterie unitaire.
    """
    tension_unitaire = float(batterie_unitaire.get("tension_v")) if batterie_unitaire and batterie_unitaire.get(
        "tension_v") is not None else None
    capacite_unitaire = float(batterie_unitaire.get("capacite_ah")) if batterie_unitaire and batterie_unitaire.get(
        "capacite_ah") is not None else None

    if not tension_unitaire or not capacite_unitaire:
        return None

    tension_systeme = float(batterie_necessaire["tension_v"])
    capacite_totale = float(batterie_necessaire["capacite_ah"])

    nb_serie = math.ceil(tension_systeme / tension_unitaire)
    nb_parallele = math.ceil(capacite_totale / capacite_unitaire)
    nb_total = nb_serie * nb_parallele

    avertissement_tension = None
    if onduleur and onduleur.get("tension_max_batterie_v"):
        tension_reelle = nb_serie * tension_unitaire
        if tension_reelle > float(onduleur["tension_max_batterie_v"]):
            avertissement_tension = (
                f"⚠️ Tension parc batterie ({tension_reelle}V) "
                f"dépasse le max onduleur ({onduleur['tension_max_batterie_v']}V)"
            )

    return {
        "nb_batteries_serie": nb_serie,
        "nb_batteries_parallele": nb_parallele,
        "nb_batteries_total": nb_total,
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
    - prix_total_installation : prix total saisi par le technicien (achat + MO)
    - production_annuelle_kwh : production annuelle estimée depuis PVGIS
    - tarif_kwh
    """

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
    puissance_panneau_wc: float = 500,
    tension_batterie_v: float = 48,
    module: dict = None,
    onduleur: dict = None,
    strings: list = None,
    batterie_unitaire: dict = None
) -> dict:
    """
        Fonction principale qui orchestre tous les calculs.

        Deux modes selon les données disponibles :
            - Mode équipements : equipements est une liste d'appareils
            - Mode factures    : conso_journaliere_kwh est la moyenne extraite des factures

        Plus il y a de données composants, plus les résultats sont précis.
    """

    # --- Détermination de la consommation journalière ---
    if equipements:
        # Mode équipements — calcul depuis la liste des appareils
        conso_j_wh = calculer_consommation_journaliere(equipements)
        puissance_totale_w = calculer_puissance_total_equipement(equipements)
        source_conso = "equipements"
    elif conso_journaliere_kwh:
        # Mode factures — consommation moyenne extraite des factures
        conso_j_wh = conso_journaliere_kwh * 1000  # kWh → Wh
        # Sans équipements on ne peut pas calculer la puissance de pointe précisément
        # On estime : puissance onduleur = conso journalière / 8h × 1.25
        puissance_totale_w = (conso_j_wh / 8) * 1.25
        source_conso = "factures"
    else:
        raise ValueError("Fournissez soit les équipements soit la consommation des factures.")

    # --- Puissance panneau ---
    # Priorité : module renseigné > valeur par défaut
    if module and module.get("puissance_crete_wc"):
        puissance_panneau_wc = module["puissance_crete_wc"]

    # --- Tension système ---
    # Priorité : onduleur > batterie unitaire > valeur par défaut
    if onduleur and onduleur.get("tension_max_batterie_v"):
        tension_batterie_v = onduleur["tension_max_batterie_v"]
    elif batterie_unitaire and batterie_unitaire.get("tension_v"):
        tension_batterie_v = batterie_unitaire["tension_v"]

    # --- Calculs de base ---
    puissance_crete = calculer_puissance_crete(conso_j_wh, hsp)
    nb_panneaux = calculer_nombre_panneaux(puissance_crete, puissance_panneau_wc)
    puissance_installee = nb_panneaux * puissance_panneau_wc
    batterie = calculer_batterie(conso_j_wh, tension_batterie_v=tension_batterie_v)

    # Onduleur : 1.25 × puissance totale des équipements
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
        # Enrichis selon disponibilité des données
        "configuration_strings": None,
        "surface_champ": None,
        "configuration_batterie": None,
        #"tableau_comparatif": calculer_tableau_comparatif(conso_j_wh, hsp)
    }

    # --- Calculs enrichis ---
    # Configurations strings (nécessite module + strings)
    if module and strings:
        result["configuration_strings"] = calculer_configuration_strings(
            nb_panneaux, module, strings
        )

    # Surface du champ
    if module and module.get("longueur_m") and module.get("largeur_m"):
        result["surface_champ"] = calculer_surface_champ(nb_panneaux, module)

    # Configuration batterie
    if batterie_unitaire:
        result["configuration_batterie"] = calculer_configuration_batterie(
            batterie, batterie_unitaire, onduleur
        )

    return result