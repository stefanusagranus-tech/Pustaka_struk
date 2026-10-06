"""
pages/0_Home.py — Halaman utama Pustaka Struk (Home / Dashboard).
"""
import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.anonim import setup_anonim_page, apply_nav_style
from utils.ui_theme import apply_theme
from utils.ui_components import (
    render_header,
    render_section_title,
    render_footer,
    metric_grid,
    render_card,
)
from utils.auth import init_auth_state

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("Pustaka Struk", "📦")
apply_theme()
apply_nav_style()
init_auth_state()

# ============================================================
# HEADER
# ============================================================
render_header(
    "Pustaka Struk",
    "Dashboard analisis struk & performa toko",
    icon="📦",
)

# ============================================================
# WELCOME
# ============================================================
user_name = st.session_state.get("user_name", "User")
render_card(
    f"""
    <h3 style="margin-top:0;color:#E6EDF3;">Halo, {user_name} 👋</h3>
    <p style="color:#8B949E;margin:0;">
        Selamat datang di <b>Pustaka Struk v2.0</b>.
        Gunakan menu di samping atau tombol di bawah untuk mulai menganalisis.
    </p>
    """
)

# ============================================================
# QUICK STATS
# ============================================================
render_section_title("Ringkasan Cepat", "📊")

db_status = "Aktif" if "db_path" in st.session_state else "Belum Upload"
db_name = st.session_state.get("db_name", "-")

metric_grid([
    {"label": "Status Database", "value": db_status,
     "sub": db_name,
     "variant": "success" if db_status == "Aktif" else "warning"},
    {"label": "Total Halaman Analisis", "value": "7", "sub": "PSM, SG, Suger, Topup, dll"},
], cols=2)

# ============================================================
# QUICK NAVIGATION
# ============================================================
render_section_title("Navigasi Cepat", "🚀")

col1, col2 = st.columns(2)
with col1:
    if st.button("📊 Dashboard", use_container_width=True, key="home_nav_dash"):
        st.switch_page("App.py")
    if st.button("📊 1 PSM per PLU", use_container_width=True, key="home_nav_psm"):
        st.switch_page("pages/1_PSM_per_PLU.py")
    if st.button("🎁 2 SG per Paket", use_container_width=True, key="home_nav_sg"):
        st.switch_page("pages/2_SG_per_Paket.py")
    if st.button("🧾 4 Suger", use_container_width=True, key="home_nav_suger"):
        st.switch_page("pages/3_struk_Suger.py")

with col2:
    if st.button("📦 3 Topup Flaz", use_container_width=True, key="home_nav_topup"):
        st.switch_page("pages/5_Topup_Flaz.py")
    if st.button("🔍 Cek Struk Detail", use_container_width=True, key="home_nav_cek"):
        st.switch_page("pages/7_Cek_Struk_Detail.py")
    if st.button("❌ Void Transaksi", use_container_width=True, key="home_nav_void"):
        st.switch_page("pages/6_Cek_Struk_Void.py")
    if st.button("📋 Manage PLU", use_container_width=True, key="home_nav_plu"):
        st.switch_page("pages/8_Manage_PLU.py")

# ============================================================
# INFO
# ============================================================
render_section_title("Info Aplikasi", "ℹ️")
render_card(
    """
    <p style="margin:0;color:#8B949E;font-size:0.85rem;">
        <b>Pustaka Struk v2.0</b> — Internal use only.<br>
        Upload database di halaman <b>Dashboard</b> terlebih dahulu sebelum
        menggunakan halaman analisis.
    </p>
    """
)

render_footer()
