"""
3_struk_Suger.py — Cek Struk (Suger).
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st

from utils.common import load_tables
from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style
from utils.nav_helper import render_back_to_dashboard, safe_stop

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("Cek Struk", "🧾")
apply_nav_style()

st.title("🧾 Cek Struk")
st.markdown("Pencarian struk berdasarkan nomor bon atau flag.")

# ============================================================
# CEK DATABASE
# ============================================================
db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Dashboard dulu untuk upload ZIP.")
    safe_stop("struk")

st.success("Database: " + st.session_state.get("db_name", ""))

# ============================================================
# MAIN
# ============================================================
try:
    dfs = load_tables(db_file, ["log_receipt_prn"])
    df_receipt = dfs.get("log_receipt_prn", pd.DataFrame())

    if df_receipt.empty:
        st.warning("Tabel log_receipt_prn kosong.")
        safe_stop("struk")

    st.info(f"Total {len(df_receipt)} struk tersedia.")

    # Search
    st.markdown("---")
    st.markdown("### 🔎 Cari Struk")

    keyword = st.text_input("Nomor Bon", placeholder="Contoh: 149")

    if keyword:
        df_filtered = df_receipt[
            df_receipt["bill_no"].astype(str).str.contains(str(keyword).strip(), na=False)
        ].copy()

        if df_filtered.empty:
            st.warning(f"Tidak ada struk dengan bon {keyword}.")
        else:
            st.success(f"Ditemukan {len(df_filtered)} struk.")
            st.dataframe(df_filtered[["bill_no", "date_tx", "user_id"]], use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 Daftar Struk")
    df_display = df_receipt[["bill_no", "date_tx", "user_id"]].head(50).copy()
    st.dataframe(df_display, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)
    safe_stop("struk")

# ============================================================
# TOMBOL BAWAH
# ============================================================
render_nav_universal("struk")
render_back_to_dashboard("struk")