"""
🏠 Home — Pusat navigasi Pustaka Struk.
Halaman ini jadi starting point buat akses semua fitur.
"""
import streamlit as st
from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style

# ============================================================
# SETUP ANONIM
# ============================================================
setup_anonim_page("Home", "🏠")
apply_nav_style()

# ============================================================
# HERO / WELCOME
# ============================================================
st.title("🏠 Pustaka Struk")
st.markdown("### Dashboard POS & Analisis Transaksi")
st.markdown("Pilih halaman di bawah buat mulai analisis.")

st.markdown("---")

# ============================================================
# KARTU-KARTU MENU
# ============================================================
st.markdown("### 📋 Menu Utama")

# Baris 1
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("#### 📊 Dashboard")
        st.caption("Ringkasan performa toko: omzet, struk, kasir, jam ramai")
        if st.button("Buka Dashboard", use_container_width=True, key="home_dashboard"):
            st.switch_page("App.py")

with col2:
    with st.container(border=True):
        st.markdown("#### 📊 1 PSM per PLU")
        st.caption("Laporan PSM berdasarkan PLU")
        if st.button("Buka PSM", use_container_width=True, key="home_psm"):
            st.switch_page("pages/1_PSM_per_PLU.py")

# Baris 2
col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.markdown("#### 🎁 2 SG per Paket")
        st.caption("Laporan Serba Gratis per paket")
        if st.button("Buka SG", use_container_width=True, key="home_sg"):
            st.switch_page("pages/2_SG_per_Paket.py")

with col4:
    with st.container(border=True):
        st.markdown("#### 📦 3 Topup Flaz")
        st.caption("Laporan topup Flaz")
        if st.button("Buka Topup", use_container_width=True, key="home_topup"):
            st.switch_page("pages/5_Topup_Flaz.py")

# Baris 3
col5, col6 = st.columns(2)

with col5:
    with st.container(border=True):
        st.markdown("#### 🧾 4 Cek Struk")
        st.caption("Cek struk berdasarkan flag")
        if st.button("Buka Cek Struk", use_container_width=True, key="home_struk"):
            st.switch_page("pages/3_struk_Suger.py")

with col6:
    with st.container(border=True):
        st.markdown("#### ❌ 5 Void Transaksi")
        st.caption("Laporan transaksi void")
        if st.button("Buka Void", use_container_width=True, key="home_void"):
            st.switch_page("pages/6_Cek_Struk_Void.py")

st.markdown("---")

# ============================================================
# INFO
# ============================================================
with st.expander("ℹ️ Tentang Aplikasi"):
    st.markdown("""
    **Pustaka Struk** — Dashboard POS & Analisis Transaksi

    **Versi:** 2.0
    **Status:** Internal use only

    **Fitur:**
    - Analisis penjualan (omzet, struk, item)
    - Rekap per kasir
    - Breakdown pembayaran (cash, debit, e-wallet)
    - Grafik jam ramai
    - Laporan PSM, SG, Topup, Void
    """)
