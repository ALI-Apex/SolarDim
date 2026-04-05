import streamlit as st


def afficher_guide():

    # ==============================
    # WORKFLOW
    # ==============================
    with st.expander("🚀 Comment utiliser Raana ?", expanded=True):
        st.markdown("""
        Raana vous guide étape par étape pour dimensionner un système photovoltaïque off-grid.
        Voici le workflow recommandé :
        """)

        etapes = [
            ("1️⃣", "Factures", "Uploadez vos factures d'électricité. L'IA extrait automatiquement votre consommation et votre tarif kWh."),
            ("2️⃣", "Équipements", "Si vous n'avez pas de factures, listez vos appareils électriques avec leur puissance et leurs heures d'utilisation."),
            ("3️⃣", "Localisation", "Entrez votre ville. L'outil récupère automatiquement les données d'ensoleillement via PVGIS."),
            ("4️⃣", "Configurations", "Renseignez les caractéristiques de vos composants (onduleur, panneaux, batteries). Plus vous renseignez, plus les résultats sont précis."),
            ("5️⃣", "Accueil", "Lancez l'analyse. Les résultats s'affichent instantanément."),
            ("6️⃣", "Analyse IA", "Consultez le rapport complet généré par l'intelligence artificielle."),
        ]

        for icone, titre, description in etapes:
            col1, col2 = st.columns([1, 8])
            with col1:
                st.markdown(f"<div style='font-size:28px; text-align:center;'>{icone}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{titre}** — {description}")

        st.info("💡 Les factures ET les équipements sont optionnels — vous pouvez utiliser l'un ou l'autre selon ce dont vous disposez.")

    # ==============================
    # NOTIONS SOLAIRES
    # ==============================
    with st.expander("☀️ Notions solaires"):

        st.markdown("### HSP — Heures de Soleil Pic")
        st.markdown("""
        L'HSP représente le nombre d'heures par jour pendant lesquelles le soleil rayonne 
        à sa puissance maximale standard (1000 W/m²). C'est une moyenne annuelle calculée 
        pour votre localisation par PVGIS.

        **Exemple :** Un HSP de 4.5 h/jour à Lomé signifie que l'ensoleillement équivaut 
        à 4h30 de soleil à pleine puissance, même si le soleil brille pendant 12h.

        **Utilisation dans le calcul :**
        """)
        st.code("Puissance crête = Consommation journalière / (HSP × Performance Ratio)", language="text")

        st.divider()

        st.markdown("### Performance Ratio (PR)")
        st.markdown("""
        Le PR représente l'efficacité réelle du système par rapport à sa puissance théorique. 
        Il tient compte des pertes dues à :
        - La chaleur des panneaux
        - Les câbles et connexions
        - L'onduleur
        - La poussière et l'ombrage partiel

        **Valeur utilisée :** 0.65 (65%) — valeur standard pour un système off-grid en Afrique de l'Ouest.
        Un système bien entretenu peut atteindre 0.70 à 0.75.
        """)

        st.divider()

        st.markdown("### Puissance crête (Wc / kWc)")
        st.markdown("""
        La puissance crête est la puissance maximale qu'un panneau peut produire dans des 
        conditions standard (1000 W/m², 25°C). Elle est notée **Wc** (Watt-crête) ou **kWc** 
        (kilowatt-crête).

        **Exemple :** Un panneau de 400 Wc produit au maximum 400W dans des conditions idéales.
        Dans la réalité, la production moyenne est inférieure à cause du PR.
        """)

        st.divider()

        st.markdown("### MPPT — Maximum Power Point Tracking")
        st.markdown("""
        L'MPPT est un algorithme intégré dans l'onduleur qui ajuste en permanence la tension 
        d'entrée pour extraire le maximum de puissance des panneaux, quelles que soient 
        les conditions d'ensoleillement.

        **Plage MPPT :** L'onduleur ne fonctionne de manière optimale que si la tension 
        des strings est dans sa plage MPPT (ex: 60V à 450V). En dehors de cette plage, 
        l'onduleur ne peut pas tracker le point de puissance maximale.
        """)

    # ==============================
    # NOTIONS STRINGS / PANNEAUX
    # ==============================
    with st.expander("⚡ Notions strings et configuration des panneaux"):

        st.markdown("### Voc, Vmp, Isc, Imp")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Voc** — Tension en circuit ouvert  
            Tension maximale du panneau quand il n'est connecté à rien.
            Utilisée pour la vérification de sécurité (ne pas dépasser Voc max de l'onduleur).

            **Vmp** — Tension au point de puissance maximale  
            Tension de fonctionnement optimal du panneau.
            Utilisée pour calculer la plage MPPT.
            """)
        with col2:
            st.markdown("""
            **Isc** — Courant de court-circuit  
            Courant maximal que peut produire le panneau.

            **Imp** — Courant au point de puissance maximale  
            Courant de fonctionnement optimal du panneau.
            Utilisé pour calculer le nombre de strings en parallèle.
            """)

        st.divider()

        st.markdown("### Configuration série / parallèle")
        st.markdown("""
        **En série** → les panneaux se connectent bout à bout, les **tensions s'additionnent** 
        mais le courant reste identique.
        """)
        st.code("Tension string = Nb panneaux en série × Vmp", language="text")

        st.markdown("""
        **En parallèle** → les panneaux se connectent côte à côte, les **courants s'additionnent** 
        mais la tension reste identique.
        """)
        st.code("Courant total = Nb strings en parallèle × Imp", language="text")

        st.divider()

        st.markdown("### Calcul du nombre de panneaux en série")
        st.markdown("""
        Le nombre de panneaux en série est contraint par la plage MPPT de l'onduleur :
        """)
        st.code("""
Nb min en série = ceil(Vmppt_min / Vmp)   → plancher MPPT
Nb max en série = floor(Vmppt_max / Vmp)  → plafond MPPT optimal
Nb max absolu   = floor(Voc_max / Voc)    → limite de sécurité absolue
        """, language="text")
        st.warning("⚠️ Ne jamais dépasser le Voc max de l'onduleur — risque de destruction de l'onduleur.")

    # ==============================
    # NOTIONS BATTERIE
    # ==============================
    with st.expander("🔋 Notions batterie"):

        st.markdown("### Profondeur de décharge (DoD)")
        st.markdown("""
        Le DoD représente le pourcentage maximal de la capacité de la batterie qu'on peut utiliser 
        sans endommager la batterie ni réduire sa durée de vie.

        | Type de batterie | DoD recommandé |
        |------------------|---------------|
        | Plomb-acide      | 50% max       |
        | AGM / GEL        | 60% max       |
        | Lithium (LiFePO4)| 80 à 95%      |

        **Valeur utilisée par défaut :** 95% (batterie lithium)
        """)

        st.divider()

        st.markdown("### Capacité de batterie nécessaire")
        st.code("""
Capacité (Ah) = (Consommation journalière × Autonomie) / (Tension système × DoD)
        """, language="text")
        st.markdown("""
        **Autonomie :** Nombre de jours pendant lesquels le système peut fonctionner 
        sans soleil. Valeur par défaut : 1 jour.
        """)

        st.divider()

        st.markdown("### Configuration série / parallèle des batteries")
        st.markdown("""
        **En série** → augmente la **tension** du parc batterie.
        """)
        st.code("Nb en série = Tension système / Tension batterie unitaire", language="text")

        st.markdown("""
        **En parallèle** → augmente la **capacité** du parc batterie.
        """)
        st.code("Nb en parallèle = Capacité totale nécessaire / Capacité batterie unitaire", language="text")

    # ==============================
    # NOTIONS RENTABILITÉ
    # ==============================
    with st.expander("💰 Notions rentabilité et lecture du graphe"):

        st.markdown("### Économies annuelles")
        st.markdown("""
        Les économies annuelles représentent le montant que vous économisez chaque année 
        en produisant votre propre électricité au lieu de l'acheter au réseau.
        """)
        st.code("""
Économies annuelles = Production annuelle (kWh) × Tarif kWh (FCFA)

Production annuelle = HSP × Puissance installée (kWc) × 365 × PR
        """, language="text")

        st.divider()

        st.markdown("### Retour sur investissement (ROI)")
        st.markdown("""
        Le ROI est le nombre d'années nécessaires pour que les économies cumulées 
        remboursent le coût total de l'installation.
        """)
        st.code("ROI (ans) = Coût total installation / Économies annuelles", language="text")

        st.divider()

        st.markdown("### Comment lire le graphe de rentabilité")
        st.markdown("""
        Le graphe montre l'évolution des **gains cumulés** sur 10 ans :

        - **Zone rouge** (valeurs négatives) → vous êtes encore en phase de remboursement
        - **Zone verte** (valeurs positives) → votre installation est rentabilisée, vous gagnez de l'argent
        - **Ligne pointillée rouge** → seuil de rentabilité (ROI)
        - **Point de croisement** → le moment exact où votre installation devient rentable

        Plus la courbe monte rapidement, plus votre installation est rentable.
        Un ROI inférieur à 5 ans est excellent, entre 5 et 8 ans est bon, au-delà de 10 ans 
        il faut revoir les paramètres.
        """)

        st.divider()

        st.markdown("### Importance du tarif kWh")
        st.markdown("""
        Le tarif kWh est le paramètre le plus influent sur la rentabilité. 
        Plus le tarif est élevé, plus votre installation est rentable rapidement.

        **Conseil :** Si vous avez des factures, le tarif est calculé automatiquement. 
        Sinon, renseignez-le manuellement dans **Configurations → Paramètres économiques**.
        """)