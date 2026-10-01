"""
utils/anonim.py
Helper untuk membuat halaman Streamlit menjadi anonim.
"""

import streamlit as st


# ============================================================
# CSS ANTI-JEJAK
# ============================================================
HIDE_STYLE = """
<style>
/* Sembunyikan header Streamlit (logo, hamburger, deploy) */
header[data-testid="stHeader"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}

/* Sembunyikan menu utama (3 titik kanan atas) */
#MainMenu {
    visibility: hidden !important;
    display: none !important;
}

/* Sembunyikan footer */
footer {
    visibility: hidden !important;
    display: none !important;
}

/* Sembunyikan badge viewer + link GitHub */
.viewerBadge_container__1QSob,
.viewerBadge_link__1S137,
.viewerBadge_text__1JaDK,
[class*="viewerBadge"] {
    display: none !important;
    visibility: hidden !important;
}

/* Sembunyikan tombol Deploy */
.stDeployButton { display: none !important; }
[data-testid="stAppDeployButton"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

/* Sembunyikan "Manage app" */
[data-testid="manage-app-button"] { display: none !important; }
button[kind="header"] { display: none !important; }
[class*="manageApp"] { display: none !important; }
[class*="ManageApp"] { display: none !important; }

/* Sembunyikan anchor link pada heading */
[data-testid="stHeaderActionElements"] {
    display: none !important;
}

/* Rapikan padding atas */
.block-container {
    padding-top: 1.5rem !important;
}
</style>
"""


# ============================================================
# CSS TOMBOL NAVIGASI
# ============================================================
NAV_BUTTON_STYLE = """
<style>
/* Tombol navigasi lebih gede */
.stButton > button {
    padding: 18px 20px !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    background: linear-gradient(135deg, #2196F3, #1565c0) !important;
    color: white !important;
    border: none !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4) !important;
}
</style>
"""


# ============================================================
# DAFTAR SEMUA HALAMAN
# ============================================================
SEMUA_HALAMAN = [
    {"id": "home",      "label": "🏠 Home",             "path": "pages/0_Home.py"},
    {"id": "dashboard", "label": "📊 Dashboard",         "path": "App.py"},
    {"id": "psm",       "label": "📊 1 PSM per PLU",     "path": "pages/1_PSM_per_PLU.py"},
    {"id": "sg",        "label": "🎁 2 SG per Paket",    "path": "pages/2_SG_per_Paket.py"},
    {"id": "topup",     "label": "📦 3 Topup Flaz",      "path": "pages/5_Topup_Flaz.py"},
    {"id": "struk",     "label": "🧾 4 Cek Struk",       "path": "pages/3_struk_Suger.py"},
    {"id": "void",      "label": "❌ 5 Void Transaksi",   "path": "pages/6_Cek_Struk_Void.py"},
]


# ============================================================
# FUNGSI UTAMA
# ============================================================
def setup_anonim_page(page_title="Dashboard POS", page_icon="📊"):
    """Setup halaman jadi anonim."""
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(HIDE_STYLE, unsafe_allow_html=True)


def hide_only():
    """Cuma inject CSS tanpa set_page_config."""
    st.markdown(HIDE_STYLE, unsafe_allow_html=True)


def apply_nav_style():
    """Apply CSS tombol navigasi (gede, biru, rapi)."""
    st.markdown(NAV_BUTTON_STYLE, unsafe_allow_html=True)


def render_header(title="Dashboard POS", subtitle=""):
    """Render header custom."""
    st.title(title)
    if subtitle:
        st.markdown(subtitle)


def render_nav_universal(current_id):
    """
    Render tombol navigasi universal.
    Halaman yang lagi aktif TIDAK ditampilkan.
    
    Args:
        current_id: ID halaman aktif ("home", "psm", "sg", dll)
    """
    st.markdown("---")
    st.markdown("### 📌 Navigasi Halaman")

    halaman_lain = [h for h in SEMUA_HALAMAN if h["id"] != current_id]

    if not halaman_lain:
        st.info("Gak ada halaman lain.")
        return

    cols = st.columns(2)
    for i, h in enumerate(halaman_lain):
        with cols[i % 2]:
            if st.button(
                h["label"],
                use_container_width=True,
                key=f"nav_{current_id}_{h['id']}"
            ):
                st.switch_page(h["path"])


def render_nav_buttons():
    """
    Versi lama (backward-compatible).
    Cuma nampilin tombol Home + Dashboard.
    """
    render_nav_universal("")


def render_back_button(target_path="pages/0_Home.py", label="🏠 Kembali ke Home"):
    """Render tombol kembali."""
    if st.button(label, key=f"back_{label}"):
        st.switch_page(target_path)


def render_footer(text="Pustaka Struk v2.0"):
    """Render footer custom."""
    st.markdown("---")
    st.markdown(
        f'<div style="text-align:center; color:#999; font-size:0.85rem; padding:20px 0;">'
        f'{text}</div>',
        unsafe_allow_html=True
    )