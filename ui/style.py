def get_css():
    return """
    <style>
        /* Supprime l'espace en haut du contenu principal */
        div[data-testid="stMainBlockContainer"] {
            padding-top: 1rem !important;
            background-color: #cacfd9 
        }
        
        /* contenu Main */
        section[data-testid="stMain"] {
           background-color: #cacfd9 !important; 
           color: black;
        }
        
        
        /* Toolbar (les boutons en haut à droite) */
        div[data-testid="stToolbar"] {
            background-color: #cacfd9 !important;
        } 
    
        
    /* ============== Formulaire ====================== */
        /* Bouton de soumission de formulaire */
        [data-testid="stFormSubmitButton"] > button {
            background-color: #1B2A4A !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 12px 24px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            width: 100% !important;
            margin-top: 12px !important;
            transition: background 0.2s !important;
            letter-spacing: 0.5px !important;
        }
        
        [data-testid="stFormSubmitButton"] > button:hover {
            background-color: #F4A300 !important;
            color: white !important;
        }
        
        [data-testid="stFormSubmitButton"] > button:active {
            background-color: #d4880a !important;
        }  
       
        
    /* =========== Labels - contenu principal ================ */
        .stTextInput label,
        .stNumberInput label,
        .stSelectbox label,
        .stRadio label,
        .stFileUploader label {
            color: #1B2A4A !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }
        
        /* Labels - sidebar uniquement en blanc */
        [data-testid="stSidebar"] .stTextInput label,
        [data-testid="stSidebar"] .stNumberInput label,
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stRadio label {
            color: white !important;
        }
        
        /* Texte général - contenu principal */
        .main p, .main span, .main div {
            color: #1B2A4A !important;
        }
        
        /* Texte général - sidebar en blanc */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: white !important;
        }

    /* ================= ONGLETS Page configuration ==================== */
        
           /* Onglets (tabs) */
        [data-testid="stTabs"] [data-testid="stTab"] {
            font-size: 15px !important;
            font-weight: 600 !important;
            padding: 10px 24px !important;
            margin-right: 8px !important;
            border-radius: 8px 8px 0 0 !important;
            color: #1B2A4A !important;
            background-color: white !important;
        }
        
        /* Onglet actif */
        [data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {
            background-color: #1B2A4A !important;
            color: white !important;
            border-bottom: 3px solid #F4A300 !important;
        }
        
        /* Onglet hover */
        [data-testid="stTabs"] [data-testid="stTab"]:hover {
            background-color: #F4F6FB !important;
            color: #F4A300 !important;
        }
        
        /* Ligne sous les onglets */
        [data-testid="stTabs"] [role="tablist"] {
            gap: 8px !important;
            border-bottom: 2px solid #1B2A4A !important;
            padding-bottom: 0 !important;
        }
        
        /* Contenu de l'onglet */
        [data-testid="stTabs"] [role="tabpanel"] {
            background-color: white !important;
            border-radius: 0 12px 12px 12px !important;
            padding: 24px !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
        }
     
    /* ================= BUTTONS =========================*/
        
       /* Boutons normaux */
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s !important;
        }
        
        /* Bouton primary (orange) */
        .stButton > button[kind="primary"] {
            background-color: #F4A300 !important;
            color: white !important;
            border: none !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            background-color: #d4880a !important;
        }
        
        /* Bouton secondary */
        .stButton > button[kind="secondary"] {
            background-color: white !important;
            color: #1B2A4A !important;
            border: 1px solid #ddd !important;
        }
        
        .stButton > button[kind="secondary"]:hover {
            border-color: #F4A300 !important;
            color: #F4A300 !important;
        } 
        
        button[data-testid="stBaseButton-secondary"] {
            background-color: white;
            
        }
        
    /* ================= Sidebar ================================ */
        section[data-testid="stSidebar"] {
            padding-top: 0rem !important;
            background-color: #070e1a;
        }
        
       /* Boutons de navigation sidebar */
        [data-testid="stSidebar"] .stButton > button {
            background-color: transparent !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
            font-size: 15px !important;
            text-align: left !important;
            margin-bottom: 4px !important;
            transition: background 0.2s !important;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: rgba(255,255,255,0.15) !important;
            color: white !important;
        }
        
        /* Bouton actif — on cible le bouton de la page courante */
        [data-testid="stSidebar"] .stButton > button:active {
            background-color: #F4A300 !important;
            color: white !important;
            font-weight: bold !important;
        } 
        
        /* Layout */
        div[data-testid="stLayoutWrapper"] {
            color: black;
        }

    /* =================== METRICS CARDS =============================== */
        /* Cards métriques */
        .metric-card {
            background: white;
            border-radius: 14px;
            padding: 20px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            border-left: 4px solid #F4A300;
            margin-bottom: 16px;
        }
        .metric-card.blue {
            background: #1B2A4A;
            color: white;
            border-left: 4px solid #F4A300;
        }
        .metric-card .label {
            font-size: 16px;
            color: #f4a300;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-card.blue .label {
            color: #aaa;
        }
        .metric-card .value {
            font-size: 26px;
            font-weight: bold;
            color: #1B2A4A;
        }
        .metric-card.blue .value {
            color: white;
        }
        .metric-card .status-ok {
            color: #27AE60;
            font-size: 12px;
            margin-top: 4px;
        }
        .metric-card .status-warn {
            color: #F4A300;
            font-size: 12px;
            margin-top: 4px;
        }
        .metric-card .status-error {
            color: #E74C3C;
            font-size: 12px;
            margin-top: 4px;
        }

    /* ================ Titre de page ======================== */
        .page-title {
            font-size: 64px;
            font-weight: bold;
            color: #070e1a;
            text-align: center;
            margin-bottom: 2px;
            letter-spacing: 1px;
        }
        
        .page-subtitle {
            font-size: 20px;
            color: #070e1a;
            text-align: center;
            margin-bottom: 32px;
        }

        /* Bouton principal orange */
        .stButton > button[kind="primary"] {
            background-color: #F4A300 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: bold !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #d4880a !important;
        }

        /* Section cards */
        .section-card {
            background: white;
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            margin-bottom: 20px;
        }

        

        /* Cacher le menu hamburger Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

    /* =================== RESPONSIVE MOBILE ====================== */
        @media (max-width: 768px) {

            /* Titres de page */
            .page-title {
                font-size: 28px !important;
                letter-spacing: 0 !important;
                margin-bottom: 4px !important;
            }
            .page-subtitle {
                font-size: 14px !important;
                margin-bottom: 16px !important;
            }

            /* Colonnes : empilées sur mobile */
            [data-testid="column"] {
                min-width: 100% !important;
                width: 100% !important;
            }

            /* Metric cards : padding réduit */
            .metric-card {
                padding: 14px !important;
                margin-bottom: 10px !important;
            }
            .metric-card .value {
                font-size: 20px !important;
            }
            .metric-card .label {
                font-size: 13px !important;
            }

            /* Section cards */
            .section-card {
                padding: 14px !important;
            }

            /* Onglets : plus compacts */
            [data-testid="stTabs"] [data-testid="stTab"] {
                font-size: 12px !important;
                padding: 6px 10px !important;
                margin-right: 4px !important;
            }
            [data-testid="stTabs"] [role="tablist"] {
                gap: 4px !important;
                flex-wrap: wrap !important;
            }
            [data-testid="stTabs"] [role="tabpanel"] {
                padding: 14px !important;
            }

            /* Tableaux résultats */
            .result-table thead th {
                font-size: 15px !important;
                padding: 8px 10px !important;
            }
            .result-table tbody td {
                font-size: 13px !important;
                padding: 8px 10px !important;
            }
            .result-table tbody td:first-child {
                width: 50% !important;
            }

            /* Inputs et boutons */
            .stButton > button {
                font-size: 14px !important;
                padding: 10px 12px !important;
            }
            [data-testid="stFormSubmitButton"] > button {
                font-size: 14px !important;
                padding: 10px 16px !important;
            }

            /* Sidebar : largeur réduite sur mobile */
            section[data-testid="stSidebar"] {
                min-width: 200px !important;
                max-width: 240px !important;
            }
            [data-testid="stSidebar"] .stButton > button {
                font-size: 13px !important;
                padding: 10px 12px !important;
            }

            /* Conteneur principal : moins de padding */
            div[data-testid="stMainBlockContainer"] {
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
            }

            /* st.metric */
            [data-testid="stMetric"] {
                padding: 8px !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 18px !important;
            }
        }
        
    /* ================== Tableaux résultats ======================*/
        .result-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }
        
        .result-table thead tr {
            background-color: #1B2A4A;
            color: white;
        }
        
        .result-table thead th {
            padding: 12px 16px;
            text-align: left;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        
        .result-table tbody tr {
            border-bottom: 1px solid #f0f0f0;
            transition: background 0.15s;
        }
        
        .result-table tbody tr:hover {
            background-color: #f8f9ff;
        }
        
        .result-table tbody tr:last-child {
            border-bottom: none;
        }
        
        .result-table tbody td {
            padding: 10px 16px;
            font-size: 18px;
            color: #444;
        }
        
        .result-table tbody td:first-child {
            color: #888;
            width: 55%;
        }
        
        .result-table tbody td strong {
            color: #1B2A4A;
        }

/* ==============================
   PAGE FACTURES
   ============================== */

        /* Zone d'upload */
        [data-testid="stFileUploader"] {
            background-color: white !important;
            border: 2px dashed #1B2A4A !important;
            border-radius: 12px !important;
            padding: 20px !important;
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: #F4A300 !important;
        }
        
        /* Tableau dataframe */
        [data-testid="stDataFrame"] {
            background-color: white !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
        }

        /* Boîtes success / warning / info / error */
        [data-testid="stAlert"] {
            border-radius: 10px !important;
            border: none !important;
        }
        
        div[data-testid="stAlertContentSuccess"] {
            background-color: #e8f5e9 !important;
            color: #1B5E20 !important;
        }
        
        div[data-testid="stAlertContentWarning"] {
            background-color: #FFF8E1 !important;
            color: #7B4F00 !important;
        }
        
        div[data-testid="stAlertContentInfo"] {
            background-color: #E8EAF6 !important;
            color: #1B2A4A !important;
        }
        
        div[data-testid="stAlertContentError"] {
            background-color: #FFEBEE !important;
            color: #B71C1C !important;
        }
        
        /* Spinner */
        [data-testid="stSpinner"] {
            color: #F4A300 !important;
        }
        
        /* Subheader */
        [data-testid="stMarkdownContainer"] h3 {
            color: #1B2A4A !important;
            font-weight: 700 !important;
            border-bottom: 2px solid #F4A300 !important;
            padding-bottom: 6px !important;
            margin-bottom: 16px !important;
        }
        
        /* Caption */
        [data-testid="stCaptionContainer"] {
            color: #666 !important;
            font-style: italic !important;
        }
        
        /* Metrics (st.metric) */
        [data-testid="stMetric"] {
            background-color: white !important;
            border-radius: 10px !important;
            padding: 12px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #888 !important;
            font-size: 12px !important;
        }
        
        [data-testid="stMetricValue"] {
            color: #1B2A4A !important;
            font-weight: bold !important;
        }

    /* =================== WIZARD BAR ====================== */
        .wizard-bar {
            display: flex;
            align-items: center;
            background: #0e1f3a;
            padding: 12px 24px;
            border-radius: 12px;
            margin-bottom: 24px;
            gap: 0;
        }
        .wizard-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            position: relative;
            cursor: pointer;
        }
        .wizard-step-circle {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: bold;
            z-index: 1;
            transition: all 0.2s;
        }
        .wizard-step-circle.done { background: #27AE60; color: white; }
        .wizard-step-circle.active { background: #F4A300; color: white; box-shadow: 0 0 0 3px rgba(244,163,0,0.3); }
        .wizard-step-circle.pending { background: #333; color: #888; }
        .wizard-step-label {
            font-size: 10px;
            margin-top: 4px;
            white-space: nowrap;
        }
        .wizard-step-label.done { color: #27AE60; }
        .wizard-step-label.active { color: #F4A300; font-weight: bold; }
        .wizard-step-label.pending { color: #666; }
        .wizard-connector {
            flex: 1;
            height: 2px;
            margin-bottom: 14px;
        }
        .wizard-connector.done { background: #27AE60; }
        .wizard-connector.pending { background: #333; }
        .wizard-nav {
            display: flex;
            justify-content: space-between;
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid #e0e0e0;
        }
        .wizard-nav-btn {
            padding: 8px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
        }

    /* =================== KPI CARDS (résultats) =================== */
        .kpi-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        .kpi-card {
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .kpi-card.dark { background: #1B2A4A; }
        .kpi-card.light { background: white; border-left: 3px solid #F4A300; }
        .kpi-card.green { background: #27AE60; }
        .kpi-card.gray { background: #f0f0f0; }
        .kpi-card .kpi-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .kpi-card.dark .kpi-label { color: #F4A300; }
        .kpi-card.light .kpi-label { color: #F4A300; }
        .kpi-card.green .kpi-label { color: #c8f5d8; }
        .kpi-card.gray .kpi-label { color: #888; }
        .kpi-card .kpi-value {
            font-size: 24px;
            font-weight: bold;
            line-height: 1.1;
        }
        .kpi-card.dark .kpi-value { color: white; }
        .kpi-card.light .kpi-value { color: #1B2A4A; }
        .kpi-card.green .kpi-value { color: white; }
        .kpi-card.gray .kpi-value { color: #555; }
        .kpi-card .kpi-sub {
            font-size: 11px;
            margin-top: 4px;
        }
        .kpi-card.dark .kpi-sub { color: #aaa; }
        .kpi-card.light .kpi-sub { color: #888; }
        .kpi-card.green .kpi-sub { color: #c8f5d8; }
        .kpi-card.gray .kpi-sub { color: #aaa; }

    /* =================== COMPONENT CARDS (résultats) =================== */
        .component-cards-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        .component-card {
            background: white;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        }
        .component-card .cc-title {
            font-size: 12px;
            font-weight: bold;
            color: #1B2A4A;
            margin-bottom: 10px;
            padding-bottom: 6px;
            border-bottom: 2px solid #F4A300;
        }
        .component-card .cc-row {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            padding: 3px 0;
            border-bottom: 1px solid #f5f5f5;
        }
        .component-card .cc-row span:first-child { color: #888; }
        .component-card .cc-row span:last-child { color: #1B2A4A; font-weight: 600; }

    /* =================== CONSUMPTION COUNTER =================== */
        .consumption-counter {
            background: #1B2A4A;
            border-radius: 12px;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .consumption-counter .cc-left .cc-label {
            font-size: 10px;
            color: #F4A300;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .consumption-counter .cc-left .cc-total {
            font-size: 28px;
            font-weight: bold;
            color: white;
        }
        .consumption-counter .cc-right { text-align: right; }
        .consumption-counter .cc-right .cc-kwh {
            font-size: 18px;
            font-weight: bold;
            color: #F4A300;
        }
        .consumption-counter .cc-right .cc-count {
            font-size: 11px;
            color: #27AE60;
        }

    /* =================== DISTRIBUTION BARS =================== */
        .distrib-bar-container { margin-bottom: 4px; }
        .distrib-bar-header {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #666;
            margin-bottom: 3px;
        }
        .distrib-bar-track {
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
        }
        .distrib-bar-fill {
            height: 100%;
            border-radius: 4px;
            background: #1B2A4A;
        }
        .distrib-bar-fill.secondary { background: #F4A300; }

    /* =================== PULSE BOUTON ANALYSE =================== */
        @keyframes pulse-orange {
            0% { box-shadow: 0 0 0 0 rgba(244,163,0,0.5); }
            70% { box-shadow: 0 0 0 10px rgba(244,163,0,0); }
            100% { box-shadow: 0 0 0 0 rgba(244,163,0,0); }
        }
        .btn-pulse > button {
            animation: pulse-orange 1.5s infinite !important;
        }

    /* =================== RESPONSIVE WIZARD MOBILE =================== */
        @media (max-width: 768px) {
            .wizard-bar { padding: 8px 12px; }
            .wizard-step-label { display: none; }
            .kpi-row { grid-template-columns: repeat(2, 1fr); }
            .component-cards-row { grid-template-columns: 1fr; }
        }
            </style>
            """
