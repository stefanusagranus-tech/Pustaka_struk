
"""
pages/1_PSM_per_PLU.py — Analisis PSM per PLU.
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

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("PSM per PLU", "📊")
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
    "PSM per PLU",
    "Analisis penjualan per PLU (Product Level Unit)",
    icon="📊",
)

# ============================================================
# KONTEN
# ============================================================
render_section_title("Filter", "🔎")

# Cek db_path
if "db_path" not in st.session_state:
    st.warning("⚠️ Belum ada database. Upload dulu di Dashboard.")
    st.stop()

# Load data
@st.cache_data(show_spinner=False)
def load_data(db_path):
    tables = ["tx_trans", "tx_tsale"]
    return load_tables(db_path, tables)

try:
    dfs = load_data(st.session_state["db_path"])
    df_trans = dfs.get("tx_trans", pd.DataFrame())
    df_sale = dfs.get("tx_tsale", pd.DataFrame())
except Exception as e:
    st.error(f"Gagal load database: {e}")
    st.stop()

if df_trans.empty:
    st.info("Tabel tx_trans kosong.")
    st.stop()

# Prepare
df_trans["date_tx"] = pd.to_datetime(df_trans["date_tx"], errors="coerce")
for c in ["price", "qty", "disc", "saving", "ppn_value"]:
    if c in df_trans.columns:
        df_trans[c] = pd.to_numeric(df_trans[c], errors="coerce").fillna(0)

# Filter tanggal
if df_trans["date_tx"].notna().any():
    min_d = df_trans["date_tx"].min().date()
    max_d = df_trans["date_tx"].max().date()
    tgl_range = st.date_input(
        "Rentang Tanggal",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
        key="psm_tgl",
    )
    if len(tgl_range) == 2:
        mask = (
            (df_trans["date_tx"].dt.date >= tgl_range[0])
            & (df_trans["date_tx"].dt.date <= tgl_range[1])
        )
        df = df_trans[mask].copy()
    else:
        df = df_trans.copy()
else:
    df = df_trans.copy()

st.caption(f"Menampilkan {len(df)} baris transaksi.")

# ============================================================
# RINGKASAN
# ============================================================
render_section_title("Ringkasan", "📈")

total_plu = df["plu"].nunique() if "plu" in df.columns else 0
total_qty = df["qty"].sum() if "qty" in df.columns else 0
total_omzet = (df["price"] * df["qty"]).sum() if "price" in df.columns else 0
total_disc = df["disc"].sum() if "disc" in df.columns else 0

metric_grid([
    {"label": "Total PLU Unik", "value": f"{total_plu:,}", "variant": "accent"},
    {"label": "Total Qty Terjual", "value": f"{int(total_qty):,}"},
    {"label": "Total Omzet", "value": f"Rp {total_omzet:,.0f}", "variant": "success"},
    {"label": "Total Diskon", "value": f"Rp {total_disc:,.0f}", "variant": "warning"},
], cols=4)

# ============================================================
# TABEL PSM per PLU
# ============================================================
render_section_title("Detail per PLU", "📋")

if "plu" in df.columns:
    psm = (
        df.groupby("plu")
        .agg(
            Total_Qty=("qty", "sum"),
            Total_Omzet=("price", lambda x: 0),  # placeholder, ganti sesuai logic
            Jumlah_Transaksi=("bill_no", "nunique"),
        )
        .reset_index()
    )
    # Hitung omzet manual
    df["_omzet"] = df["price"] * df["qty"]
    psm = (
        df.groupby("plu")
        .agg(
            Total_Qty=("qty", "sum"),
            Total_Omzet=("_omzet", "sum"),
            Total_Disc=("disc", "sum"),
            Jumlah_Transaksi=("bill_no", "nunique"),
        )
        .reset_index()
        .sort_values("Total_Omzet", ascending=False)
    )
    psm.columns = ["PLU", "Qty", "Omzet", "Diskon", "Jml Transaksi"]

    # Search
    keyword = st.text_input("🔎 Cari PLU:", placeholder="Contoh: 4279272")
    if keyword:
        psm = psm[psm["PLU"].astype(str).str.contains(str(keyword), na=False)]

    st.dataframe(psm, use_container_width=True, hide_index=True)

    # Download
    csv = psm.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download PSM per PLU (CSV)",
        data=csv,
        file_name="psm_per_plu.csv",
        mime="text/csv",
    )
else:
    st.warning("Kolom `plu` tidak ditemukan di tx_trans.")

# ============================================================
# FOOTER
# ============================================================
render_footer()
