"""
pages/0b_idea_box.py — Halaman Idea Box.
"""
import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.anonim import setup_anonim_page, apply_nav_style
from utils.ui_theme import apply_theme
from utils.ui_components import render_page_header, render_footer
from utils.auth import init_auth_state
from utils.idea_box_view import render_idea_box

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("Idea Box", "💡")
apply_theme()
apply_nav_style()
init_auth_state()

if not st.session_state.get("logged_in", False):
    st.warning("Silakan login dulu di halaman utama.")
    st.stop()

# ============================================================
# HEADER
# ============================================================
render_page_header(
    "Idea Box",
    "Tulis ide → auto-generate blueprint → copy ke AI lain",
    icon="💡",
)

# ============================================================
# KONTEN (delegate ke util)
# ============================================================
render_idea_box()

# ============================================================
# FOOTER
# ============================================================
render_footer()
