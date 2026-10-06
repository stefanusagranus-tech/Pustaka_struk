"""
pages/6_Cek_Struk_Void.py — Cek & void transaksi.
"""
import os
import sys

import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.anonim import setup_anonim_page, apply_nav_style
from utils.ui_theme import apply_theme
from utils.ui_components import (
    render_page_header,
    render_footer,
    render_section_title,
    metric_grid,
)
from utils.auth import init_auth_state
from utils.common import load_tables

setup_anonim_page("Cek Struk Void", "❌")
apply_theme()
apply_nav_style()
init_auth_state()

if not st.session_state.get("logged_in", False):
    st.warning("Silakan login dulu di halaman utama.")
    st.stop()

render_page_header(
    "Cek Struk Void",
    "Cari & periksa transaksi yang di-void",
    icon="❌",
)

# ============================================================
# KONTEN
# ============================================================
if "db_path" not in st.session_state:
    st.warning("⚠️ Belum ada database. Upload dulu di Dashboard.")
    st.stop()

@st.cache_data(show_spinner=False)
def load_data(db_path):
    tables = ["tx_tsale", "tx_trans", "log_et_reversal", "log_trans_sync"]
    return load_tables(db_path, tables)

try:
    dfs = load_data(st.session_state["db_path"])
    df_sale = dfs.get("tx_tsale", pd.DataFrame())
    df_reversal = dfs.get("log_et_reversal", pd.DataFrame())
except Exception as e:
    st.error(f"Gagal load database: {e}")
    st.stop()

# Ringkasan
render_section_title("Ringkasan Void", "📈")

total_void = len(df_reversal) if not df_reversal.empty else 0

metric_grid([
    {"label": "Total Void", "value": f"{total_void:,}", "variant": "danger"},
], cols=1)

# Pencarian faktur
render_section_title("Cari Faktur", "🔎")
faktur_input = st.text_input("Masukkan nomor faktur:", placeholder="Contoh: 119-27090149")

if faktur_input:
    # Cek di tx_tsale
    if not df_sale.empty and "faktur" in df_sale.columns:
        result = df_sale[df_sale["faktur"].astype(str).str.contains(faktur_input, na=False)]
        if not result.empty:
            st.success(f"✅ Faktur ditemukan di tx_tsale ({len(result)} baris)")
            st.dataframe(result, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Faktur tidak ditemukan di tx_tsale.")

    # Cek di log_et_reversal
    if not df_reversal.empty and "faktur" in df_reversal.columns:
        result_rev = df_reversal[df_reversal["faktur"].astype(str).str.contains(faktur_input, na=False)]
        if not result_rev.empty:
            st.error(f"❌ Faktur ada di log reversal ({len(result_rev)} baris)")
            st.dataframe(result_rev, use_container_width=True, hide_index=True)

# Tabel void
render_section_title("Daftar Void", "📋")
if not df_reversal.empty:
    st.dataframe(df_reversal, use_container_width=True, hide_index=True)
    csv = df_reversal.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Daftar Void (CSV)",
        data=csv,
        file_name="daftar_void.csv",
        mime="text/csv",
    )
else:
    st.info("Tidak ada data void.")

render_footer()
