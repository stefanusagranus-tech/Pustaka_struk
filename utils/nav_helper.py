"""
utils/nav_helper.py
Helper untuk tombol navigasi balik ke Dashboard.
Aman dipakai walau data kosong / error / st.stop().
"""
import streamlit as st


def render_back_to_dashboard(key_suffix="default", label="🏠 Kembali ke Dashboard"):
    """
    Render tombol kembali ke Dashboard (App.py).
    Aman dipakai di semua kondisi.

    Args:
        key_suffix: string unik (biasanya nama halaman)
        label: teks tombol
    """
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(label, use_container_width=True, key=f"back_to_dash_{key_suffix}"):
            st.switch_page("App.py")


def render_back_to_menu(key_suffix="default", label="🏠 Kembali ke Menu Utama"):
    """Render tombol kembali ke menu utama (App.py)."""
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(label, use_container_width=True, key=f"back_to_menu_{key_suffix}"):
            st.switch_page("App.py")


def safe_stop(key_suffix="default"):
    """
    Ganti st.stop() dengan ini.
    Tetap render tombol back sebelum stop.
    """
    render_back_to_dashboard(key_suffix, label="🏠 Kembali ke Dashboard")
    st.stop()


def render_back_buttons(key_suffix="default"):
    """
    Render 2 tombol: Dashboard + Menu.
    Cocok ditaruh di paling bawah halaman.
    """
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "🏠 Kembali ke Dashboard",
            use_container_width=True,
            key=f"back_dash_{key_suffix}",
        ):
            st.switch_page("App.py")
    with col2:
        if st.button(
            "📋 Kembali ke Menu",
            use_container_width=True,
            key=f"back_menu_{key_suffix}",
        ):
            st.switch_page("App.py")
