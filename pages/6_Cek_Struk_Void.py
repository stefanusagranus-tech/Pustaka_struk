"""
6_Cek_Struk_Void.py — Laporan Void Transaksi.
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
setup_anonim_page("Laporan Void Transaksi", "❌")
apply_nav_style()

st.title("❌ Laporan Void Transaksi")
st.markdown("Menampilkan transaksi yang dibatalkan (void) dari `tx_trans`.")

# ============================================================
# CEK DATABASE
# ============================================================
db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Dashboard dulu untuk upload ZIP.")
    safe_stop("void")

st.success("Database: " + st.session_state.get("db_name", ""))

# ============================================================
# MAIN
# ============================================================
try:
    dfs = load_tables(db_file, ["tx_trans"])
    df_trans = dfs.get("tx_trans", pd.DataFrame())

    if df_trans.empty:
        st.info("Tabel tx_trans kosong.")
        safe_stop("void")

    # Cari void
    df_void = pd.DataFrame()

    if "flag" in df_trans.columns:
        df_void = df_trans[
            df_trans["flag"].astype(str).str.upper().isin(["V", "VOID", "1"])
        ].copy()

    if df_void.empty and "flag_return" in df_trans.columns:
        df_void = df_trans[
            df_trans["flag_return"].astype(str).str.upper().isin(["T", "TRUE", "1", "Y"])
        ].copy()

    if df_void.empty:
        st.info("Tidak ada data void di database ini.")
        safe_stop("void")

    # Normalisasi
    for c in ["qty", "price", "disc"]:
        if c in df_void.columns:
            df_void[c] = pd.to_numeric(df_void[c], errors="coerce").fillna(0)

    df_void["total"] = df_void["price"] * df_void["qty"]

    # KPI
    total_void = df_void["bill_no"].nunique() if "bill_no" in df_void.columns else len(df_void)
    total_item = len(df_void)
    total_qty = int(df_void["qty"].sum()) if "qty" in df_void.columns else 0
    total_nilai = df_void["total"].sum() if "total" in df_void.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🧾 Total Struk Void", format(total_void, ","))
    c2.metric("📦 Total Item", format(total_item, ","))
    c3.metric("🔢 Total Qty", format(total_qty, ","))
    c4.metric("💰 Total Nilai", "Rp " + format(total_nilai, ",.0f"))

    st.markdown("---")

    # Tabel
    display_cols = [c for c in ["date_tx", "bill_no", "user_id", "plu", "qty", "price", "total"] if c in df_void.columns]
    if display_cols:
        st.dataframe(df_void[display_cols], use_container_width=True, hide_index=True)
    else:
        st.dataframe(df_void, use_container_width=True, hide_index=True)

    st.download_button(
        "📥 Download Void (CSV)",
        data=df_void.to_csv(index=False).encode("utf-8"),
        file_name="void_transaksi.csv",
        mime="text/csv",
    )

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)
    safe_stop("void")

# ============================================================
# TOMBOL BAWAH
# ============================================================
render_nav_universal("void")
render_back_to_dashboard("void")