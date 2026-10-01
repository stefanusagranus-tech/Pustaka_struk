"""
404.py — Halaman tidak ditemukan.
"""
import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.anonim import setup_anonim_page, apply_nav_style

# Setup
setup_anonim_page("404 - Tidak Ditemukan", "🔍")
apply_nav_style()

# Konten
st.markdown("""
<div style="text-align: center; padding: 80px 20px;">
    <h1 style="font-size: 8rem; margin: 0; color: #2196F3;">404</h1>
    <h2 style="margin: 20px 0;">⚠️ TERDETEKSI KARBIT ⚠️</h2>
    <p style="color: #888; font-size: 1.1rem;">
        YAHAA KARBIT, BELAJAR DULU ALBUM NYA BOS.
    </p>
</div>
""", unsafe_allow_html=True)
