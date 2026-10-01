"""
0_Home.py — Pusat upload database.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from utils.anonim import setup_anonim_page, apply_nav_style
from utils.nav_helper import render_back_to_dashboard

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("Home", "🏠")
apply_nav_style()

st.title("🏠 Pustaka Struk")
st.markdown("Upload database ZIP untuk mulai analisis.")

# ============================================================
# INFO
# ============================================================
st.markdown("---")
st.info("💡 Upload database di halaman **Dashboard**. Halaman ini cuma info.")

# ============================================================
# TOMBOL BACK
# ============================================================
render_back_to_dashboard("home")