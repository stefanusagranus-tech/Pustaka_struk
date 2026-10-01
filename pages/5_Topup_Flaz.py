"""
5_Topup_Flaz.py — Laporan Topup Flaz.
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
setup_anonim_page("Topup Flaz", "📦")
apply_nav_style()

st.title("📦 Laporan Topup Flaz")
st.markdown("Menampilkan transaksi topup Flaz dari database.")

# ============================================================
# CEK DATABASE
# ============================================================
db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Dashboard dulu untuk upload ZIP.")
    safe_stop("topup")

st.success("Database: " + st.session_state.get("db_name", ""))

# ============================================================
# MAIN
# ============================================================
try:
    dfs = load_tables(db_file, ["tx_tsale", "tx_trans"])
    df_sale = dfs.get("tx_tsale", pd.DataFrame())
    df_trans = dfs.get("tx_trans", pd.DataFrame())

    # Cari topup flaz
    df_topup = pd.DataFrame()

    if not df_sale.empty and "id_topup" in df_sale.columns:
        df_topup = df_sale[df_sale["id_topup"].notna()].copy()
    elif not df_sale.empty and "pk_topup" in df_sale.columns:
        df_topup = df_sale[df_sale["pk_topup"].notna()].copy()

    if df_topup.empty:
        st.info("Tidak ada data topup Flaz di database ini.")
        safe_stop("topup")

    # KPI
    total_topup = len(df_topup)
    total_nominal = pd.to_numeric(
        df_topup.get("nom_topup", 0), errors="coerce"
    ).fillna(0).sum()

    c1, c2 = st.columns(2)
    c1.metric("Total Topup", format(total_topup, ","))
    c2.metric("Total Nominal", "Rp " + format(total_nominal, ",.0f"))

    st.markdown("---")

    # Tabel
    cols_show = [c for c in ["date_tx", "user_id", "faktur", "id_topup", "nom_topup"] if c in df_topup.columns]
    if cols_show:
        st.dataframe(df_topup[cols_show], use_container_width=True, hide_index=True)

    st.download_button(
        "📥 Download Detail Topup Flaz (CSV)",
        data=df_topup.to_csv(index=False).encode("utf-8"),
        file_name="topup_flaz.csv",
        mime="text/csv",
    )

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)
    safe_stop("topup")

# ============================================================
# TOMBOL BAWAH
# ============================================================
render_nav_universal("topup")
render_back_to_dashboard("topup")