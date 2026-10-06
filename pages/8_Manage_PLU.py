"""
pages/8_Manage_PLU.py — Halaman Manage PLU.
"""
import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.anonim import setup_anonim_page, apply_nav_style
from utils.ui_theme import apply_theme
from utils.ui_components import render_footer
from utils.auth import init_auth_state
from utils.manage_plu_view import render_manage_plu

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("Manage PLU", "📋")
apply_theme()
apply_nav_style()
init_auth_state()

if not st.session_state.get("logged_in", False):
    st.warning("Silakan login dulu di halaman utama.")
    st.stop()

# ============================================================
# KONTEN (delegate ke util)
# ============================================================
render_manage_plu()

# ============================================================
# FOOTER
# ============================================================
render_footer()
