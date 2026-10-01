"""
utils/anonim.py
Helper untuk membuat halaman Streamlit menjadi anonim.
Import di setiap file pages/*.py:

    from utils.anonim import setup_anonim_page, render_nav_buttons, render_header

    setup_anonim_page("Nama Halaman", "📊")
    render_header("📊 Judul Halaman", "Deskripsi singkat")
    # ... konten halaman ...
    render_nav_buttons()
"""

import streamlit as st


# ============================================================
# CSS ANTI-JEJAK (Hide branding Streamlit + GitHub + Cloud overlay)
# ============================================================
HIDE_STYLE = """
<style>
/* --- Sembunyikan header Streamlit (logo, hamburger, deploy) --- */
header[data-testid="stHeader"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}

/* --- Sembunyikan menu utama (3 titik kanan atas) --- */
#MainMenu {
    visibility: hidden !important;
    display: none !important;
}

/* --- Sembunyikan footer --- */
footer {
    visibility: hidden !important;
    display: none !important;
}

/* --- Sembunyikan badge viewer + link GitHub --- */
.viewerBadge_container__1QSob,
.viewerBadge_link__1S137,
.viewerBadge_text__1JaDK,
[class*="viewerBadge"] {
    display: none !important;
    visibility: hidden !important;
}

/* --- Sembunyikan tombol Deploy --- */
.stDeployButton { display: none !important; }
[data-testid="stAppDeployButton"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

/* --- Sembunyikan "Manage app" (Streamlit Cloud overlay) --- */
[data-testid="manage-app-button"] { display: none !important; }
button[kind="header"] { display: none !important; }
[class*="manageApp"] { display: none !important; }
[class*="ManageApp"] { display: none !important; }

/* --- Sembunyikan anchor link pada heading --- */
[data-testid="stHeaderActionElements"] {
    display: none !important;
}

/* --- Rapikan padding atas karena header disembunyikan --- */
.block-container {
    padding-top: 1.5rem !important;
}
</style>
"""


# ============================================================
# FUNGSI UTAMA
# ============================================================
def setup_anonim_page(page_title="Dashboard POS", page_icon="📊"):
    """
    Setup halaman jadi anonim.
    
    Args:
        page_title: Judul halaman (muncul di tab browser)
        page_icon: Emoji icon (muncul di tab browser)
    
    Panggil di PALING ATAS file pages/*.py
    """
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Inject CSS anti-jejak
    st.markdown(HIDE_STYLE, unsafe_allow_html=True)


def render_header(title="Dashboard POS", subtitle=""):
    """
    Render header custom (judul + subtitle).
    
    Args:
        title: Judul halaman
        subtitle: Subjudul / deskripsi (opsional)
    """
    st.title(title)
    if subtitle:
        st.markdown(subtitle)


def render_nav_buttons():
    """
    Render tombol navigasi custom di bawah halaman.
    Jadi user bisa pindah halaman tanpa perlu sidebar.
    """
    st.markdown("---")
    st.markdown("### 📌 Navigasi Halaman")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Dashboard", use_container_width=True, key="nav_home"):
            st.switch_page("App.py")
        if st.button("📊 1 PSM per PLU", use_container_width=True, key="nav_psm"):
            st.switch_page("pages/1_PSM_per_PLU.py")
        if st.button("🎁 2 SG per Paket", use_container_width=True, key="nav_sg"):
            st.switch_page("pages/2_SG_per_Paket.py")
    
    with col2:
        if st.button("📦 3 Topup Flaz", use_container_width=True, key="nav_topup"):
            st.switch_page("pages/5_Topup_Flaz.py")
        if st.button("🧾 4 Cek Struk", use_container_width=True, key="nav_struk"):
            st.switch_page("pages/3_struk_Suger.py")
        if st.button("❌ 5 Void Transaksi", use_container_width=True, key="nav_void"):
            st.switch_page("pages/6_Cek_Struk_Void.py")
    
    with col3:
        if st.button("ℹ️ Tentang", use_container_width=True, key="nav_about"):
            st.info("Dashboard POS v2.0 — Internal use only")
        if st.button("📖 Bantuan", use_container_width=True, key="nav_help"):
            st.info("Hubungi admin untuk bantuan teknis")


# ============================================================
# FUNGSI BONUS (opsional, kalau butuh)
# ============================================================
def hide_only():
    """
    Cuma inject CSS tanpa set_page_config.
    Berguna kalau kamu mau pakai set_page_config sendiri.
    """
    st.markdown(HIDE_STYLE, unsafe_allow_html=True)


def render_footer(text="Dashboard POS v2.0"):
    """Render footer custom (opsional, karena footer default disembunyikan)."""
    st.markdown("---")
    st.markdown(
        f'<div style="text-align:center; color:#999; font-size:0.85rem; padding:20px 0;">'
        f'{text}</div>',
        unsafe_allow_html=True
    )
