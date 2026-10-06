"""
ui_theme.py — Tema & CSS global untuk Pustaka Struk.
Semua styling di sini biar App.py & pages tetap bersih.
"""
import streamlit as st


# Palet warna profesional (dark navy + accent teal)
COLORS = {
    "bg":          "#0E1117",
    "surface":     "#161B22",
    "surface_alt": "#1C2128",
    "border":      "#30363D",
    "text":        "#E6EDF3",
    "text_muted":  "#8B949E",
    "accent":      "#2F81F7",
    "accent_soft": "#1F6FEB",
    "success":     "#3FB950",
    "warning":     "#D29922",
    "danger":      "#F85149",
}


def apply_theme():
    """Inject CSS global. Panggil sekali di App.py & tiap page."""
    st.markdown(
        f"""
        <style>
        /* ---------- Base ---------- */
        .stApp {{
            background-color: {COLORS['bg']};
        }}
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: {COLORS['text']};
        }}

        /* ---------- Sembunyikan elemen default Streamlit ---------- */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stDeployButton {{display: none;}}

        /* ---------- Container ---------- */
        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }}

        /* ---------- Header ---------- */
        .app-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem 1.25rem;
            background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['surface_alt']} 100%);
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }}
        .app-header h1 {{
            font-size: 1.35rem;
            font-weight: 700;
            margin: 0;
            color: {COLORS['text']};
            letter-spacing: -0.02em;
        }}
        .app-header p {{
            margin: 0.15rem 0 0 0;
            font-size: 0.85rem;
            color: {COLORS['text_muted']};
        }}

        /* ---------- Section title ---------- */
        .section-title {{
            font-size: 1.05rem;
            font-weight: 600;
            color: {COLORS['text']};
            margin: 1.5rem 0 0.75rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid {COLORS['border']};
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        /* ---------- Metric Card ---------- */
        .metric-card {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 1rem 1.1rem;
            transition: border-color 0.15s ease, transform 0.15s ease;
        }}
        .metric-card:hover {{
            border-color: {COLORS['accent_soft']};
            transform: translateY(-1px);
        }}
        .metric-card .label {{
            font-size: 0.78rem;
            font-weight: 500;
            color: {COLORS['text_muted']};
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
        }}
        .metric-card .value {{
            font-size: 1.45rem;
            font-weight: 700;
            color: {COLORS['text']};
            letter-spacing: -0.02em;
            line-height: 1.2;
        }}
        .metric-card .value.accent {{ color: {COLORS['accent']}; }}
        .metric-card .value.success {{ color: {COLORS['success']}; }}
        .metric-card .value.warning {{ color: {COLORS['warning']}; }}
        .metric-card .value.danger  {{ color: {COLORS['danger']}; }}
        .metric-card .sub {{
            font-size: 0.75rem;
            color: {COLORS['text_muted']};
            margin-top: 0.3rem;
        }}

        /* ---------- Card (generic) ---------- */
        .card {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 1.1rem 1.25rem;
            margin-bottom: 1rem;
        }}

        /* ---------- Pill / badge ---------- */
        .pill {{
            display: inline-block;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 600;
            background: {COLORS['surface_alt']};
            color: {COLORS['text_muted']};
            border: 1px solid {COLORS['border']};
        }}
        .pill.accent {{ color: {COLORS['accent']}; border-color: {COLORS['accent_soft']}; }}
        .pill.success {{ color: {COLORS['success']}; }}
        .pill.warning {{ color: {COLORS['warning']}; }}
        .pill.danger  {{ color: {COLORS['danger']}; }}

        /* ---------- Button ---------- */
        .stButton > button {{
            border-radius: 8px;
            border: 1px solid {COLORS['border']};
            background: {COLORS['surface']};
            color: {COLORS['text']};
            font-weight: 500;
            transition: all 0.15s ease;
        }}
        .stButton > button:hover {{
            border-color: {COLORS['accent']};
            background: {COLORS['surface_alt']};
            color: {COLORS['accent']};
        }}
        .stButton > button[kind="primary"] {{
            background: {COLORS['accent']};
            border-color: {COLORS['accent']};
            color: white;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: {COLORS['accent_soft']};
            color: white;
        }}

        /* ---------- DataFrame ---------- */
        .stDataFrame {{
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid {COLORS['border']};
        }}

        /* ---------- Tabs ---------- */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.25rem;
            border-bottom: 1px solid {COLORS['border']};
        }}
        .stTabs [data-baseweb="tab"] {{
            padding: 0.5rem 1rem;
            font-size: 0.88rem;
            font-weight: 500;
            color: {COLORS['text_muted']};
        }}
        .stTabs [aria-selected="true"] {{
            color: {COLORS['accent']};
        }}

        /* ---------- Divider ---------- */
        hr {{
            border-color: {COLORS['border']};
            margin: 1.25rem 0;
        }}

        /* ---------- Caption ---------- */
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: {COLORS['text_muted']};
            font-size: 0.8rem;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )
