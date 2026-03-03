"""
Custom CSS styling for the Robot Vacuum Depot application.
Professional light mode theme with modern UI.
"""


def get_dark_mode_css() -> str:
    """Returns light mode CSS for modern, professional UI."""
    return """
    <style>
        /* ============================================
           GLOBAL LIGHT THEME
           ============================================ */
        .stApp {
            background-color: #FFFFFF;
            color: #31333F;
        }
        
        .main .block-container {
            background-color: #FFFFFF;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        
        /* ============================================
           TYPOGRAPHY
           ============================================ */
        h1, h2, h3, h4, h5, h6 {
            color: #31333F;
        }
        
        p, div, span {
            color: #31333F;
        }
        
        /* ============================================
           SIDEBAR - LIGHT THEME
           ============================================ */
        [data-testid="stSidebar"] {
            background-color: #F8F9FA;
            color: #31333F;
        }
        
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #31333F;
        }
        
        [data-testid="stSidebar"] p {
            color: #5F6368;
        }
        
        .sidebar-branding {
            text-align: center;
            padding: 1rem 0;
            margin-bottom: 1rem;
            border-bottom: 2px solid #E0E0E0;
        }
        
        .sidebar-title {
            font-size: 1.8rem;
            font-weight: 800;
            color: #31333F;
            margin: 0;
            letter-spacing: -0.01em;
        }
        
        .sidebar-tagline {
            font-size: 0.9rem;
            color: #5F6368;
            margin: 0.25rem 0 0 0;
        }
        
        /* ============================================
           CHAT MESSAGES - iMessage Style (Light Mode)
           ============================================ */
        .stChatMessage {
            padding: 0.75rem 1rem;
        }
        
        /* User messages - Light Blue, Right-aligned */
        [data-testid="stChatMessage"][data-message-author="user"] {
            background-color: #FFFFFF;
        }
        
        [data-testid="stChatMessage"][data-message-author="user"] .stChatMessageContent {
            background-color: #bfe1ff;
            color: #1a1a1a;
            border-radius: 18px 18px 4px 18px;
            padding: 0.75rem 1rem;
            margin-left: auto;
            max-width: 70%;
            text-align: left;
        }
        
        /* Assistant messages - Light Gray, Left-aligned */
        [data-testid="stChatMessage"][data-message-author="assistant"] {
            background-color: #FFFFFF;
        }
        
        [data-testid="stChatMessage"][data-message-author="assistant"] .stChatMessageContent {
            background-color: #F0F2F6;
            color: #31333F;
            border-radius: 18px 18px 18px 4px;
            padding: 0.75rem 1rem;
            margin-right: auto;
            max-width: 70%;
        }
        
        /* ============================================
           BUTTONS
           ============================================ */
        .stButton > button {
            background-color: #bfe1ff;
            color: #1a1a1a;
            border: 1px solid #bfe1ff;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .stButton > button:hover {
            background-color: #9dd1ff;
            border-color: #9dd1ff;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(191, 225, 255, 0.4);
        }
        
        /* ============================================
           WELCOME SCREEN QUERY CARDS (Action Cards)
           ============================================ */
        .query-card {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0.75rem 0;
            cursor: pointer;
            transition: all 0.3s ease;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            position: relative;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .query-card:hover {
            background: #F8F9FA;
            border-color: #bfe1ff;
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(191, 225, 255, 0.3);
        }
        
        .query-card-icon {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .query-card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #31333F;
            line-height: 1.4;
        }
        
        /* Style welcome screen buttons to look like cards */
        .main .block-container .stButton > button[type="secondary"] {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 12px;
            padding: 1.5rem;
            min-height: 120px;
            font-size: 1.1rem;
            font-weight: 600;
            color: #31333F;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .main .block-container .stButton > button[type="secondary"]:hover {
            background: #F8F9FA;
            border-color: #bfe1ff;
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(191, 225, 255, 0.3);
            color: #1a73e8;
        }
        
        /* ============================================
           TABS - LIGHT THEME
           ============================================ */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #FFFFFF;
            border-bottom: 1px solid #E0E0E0;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #5F6368;
            background-color: #FFFFFF;
        }
        
        .stTabs [aria-selected="true"] {
            color: #1a73e8;
            background-color: #FFFFFF;
        }
        
        /* ============================================
           CODE BLOCKS
           ============================================ */
        .stCodeBlock {
            background-color: #F8F9FA;
            border: 1px solid #E0E0E0;
        }
        
        /* ============================================
           EXPANDERS
           ============================================ */
        .streamlit-expanderHeader {
            background-color: #F8F9FA;
            color: #31333F;
        }
        
        .streamlit-expanderContent {
            background-color: #FFFFFF;
            color: #31333F;
        }
        
        /* ============================================
           DATA FRAMES
           ============================================ */
        .stDataFrame {
            background-color: #FFFFFF;
        }
        
        /* ============================================
           INPUT FIELDS
           ============================================ */
        .stTextInput > div > div > input {
            background-color: #FFFFFF;
            color: #31333F;
            border: 1px solid #E0E0E0;
        }
        
        /* ============================================
           CHAT INPUT BOX - MODERN ROUNDED DESIGN
           ============================================ */
        /* Main input container - rounded pill shape */
        div[data-testid="stChatInputContainer"] {
            background-color: #FFFFFF !important;
            padding: 0.5rem 0 !important;
        }
        
        div[data-testid="stChatInput"] {
            background-color: #F8F9FA !important;
            border-radius: 24px !important; /* Pill-shaped */
            border: 1px solid #E0E0E0 !important;
            padding: 0.5rem 1rem !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
            transition: all 0.2s ease !important;
        }
        
        div[data-testid="stChatInput"]:focus-within {
            border-color: #bfe1ff !important;
            box-shadow: 0 4px 12px rgba(191, 225, 255, 0.25) !important;
        }
        
        /* Textarea inside - remove default styling, make it blend */
        div[data-testid="stChatInput"] textarea {
            background-color: transparent !important;
            color: #31333F !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 0.5rem 0 !important;
            font-size: 0.95rem !important;
            line-height: 1.5 !important;
            resize: none !important;
            box-shadow: none !important;
        }
        
        div[data-testid="stChatInput"] textarea:focus {
            outline: none !important;
            box-shadow: none !important;
        }
        
        div[data-testid="stChatInput"] textarea::placeholder {
            color: #9AA0A6 !important;
        }
        
        /* Send button - rounded and modern */
        div[data-testid="stChatInput"] button {
            background-color: #bfe1ff !important;
            border-radius: 50% !important; /* Circular */
            width: 36px !important;
            height: 36px !important;
            min-width: 36px !important;
            padding: 0 !important;
            border: none !important;
            box-shadow: 0 2px 4px rgba(191, 225, 255, 0.4) !important;
            transition: all 0.2s ease !important;
        }
        
        div[data-testid="stChatInput"] button:hover {
            background-color: #9dd1ff !important;
            box-shadow: 0 4px 8px rgba(191, 225, 255, 0.5) !important;
            transform: scale(1.05) !important;
        }
        
        div[data-testid="stChatInput"] button:active {
            transform: scale(0.95) !important;
        }
        
        /* Alternative targeting for compatibility */
        .stChatInputContainer {
            background-color: #FFFFFF !important;
            padding: 0.5rem 0 !important;
        }
        
        .stChatInputContainer > div {
            background-color: #F8F9FA !important;
            border-radius: 24px !important;
            border: 1px solid #E0E0E0 !important;
            padding: 0.5rem 1rem !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
        }
        
        .stChatInputContainer textarea {
            background-color: transparent !important;
            color: #31333F !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 0.5rem 0 !important;
        }
        
        .stChatInputContainer textarea::placeholder {
            color: #9AA0A6 !important;
        }
        
        /* ============================================
           WELCOME SECTION
           ============================================ */
        .welcome-section {
            margin: 2rem 0;
            padding: 2rem;
            background: linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%);
            border-radius: 12px;
            border: 1px solid #E0E0E0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        .welcome-heading {
            font-size: 2.5rem;
            font-weight: 700;
            color: #31333F;
            margin: 0 0 0.5rem 0;
        }
        
        .welcome-text {
            font-size: 1.1rem;
            color: #5F6368;
            margin: 0 0 1.5rem 0;
        }
        
        /* ============================================
           STATUS INDICATOR
           ============================================ */
        [data-testid="stStatus"] {
            background-color: #F8F9FA;
            border: 1px solid #E0E0E0;
        }
        
        /* ============================================
           SUCCESS/INFO MESSAGES
           ============================================ */
        .stSuccess {
            background-color: #E8F5E9;
            border: 1px solid #4CAF50;
            color: #2E7D32;
        }
        
        .stInfo {
            background-color: #E3F2FD;
            border: 1px solid #2196F3;
            color: #1565C0;
        }
        
        .stError {
            background-color: #FFEBEE;
            border: 1px solid #F44336;
            color: #C62828;
        }
    </style>
    """
