"""
App.py — Pustaka Struk Main App (routing only).
Semua logic ada di utils/.
"""
import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.anonim import setup_anonim_page, apply_nav_style
from utils.auth import (
    init_auth_state,
    render_login_screen,
    render_menu_screen,
    logout,
    back_to_menu,
)
from utils.ui_theme import apply_theme
from utils.ui_components import render_footer
from utils.dashboard_view import render_dashboard
from utils.idea_box_view import render_idea_box
from utils.manage_plu_view import render_manage_plu

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("Pustaka Struk", "📦")
apply_theme()
apply_nav_style()
init_auth_state()

# ============================================================
# ROUTING
# ============================================================
if not st.session_state.logged_in:
    render_login_screen()
    st.stop()

if st.session_state.current_page is None:
    render_menu_screen()
    st.stop()

# Top bar
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    page_map = {
        "dashboard": "📊 Dashboard",
        "idea_box": "💡 Idea Box",
        "manage_plu": "📋 Manage PLU",
    }
    page_name = page_map.get(st.session_state.current_page, "📄 Halaman")
    st.markdown(f"### {page_name}")
with col2:
    if st.button("⬅️ Menu", use_container_width=True, key="top_back"):
        back_to_menu()
with col3:
    if st.button("🚪 Logout", use_container_width=True, key="top_logout"):
        logout()

st.markdown("---")

# ============================================================
# HALAMAN
# ============================================================
if st.session_state.current_page == "dashboard":
    render_dashboard()

elif st.session_state.current_page == "idea_box":
    render_idea_box()

elif st.session_state.current_page == "manage_plu":
    render_manage_plu()

# ============================================================
# FOOTER
# ============================================================
render_footer()
