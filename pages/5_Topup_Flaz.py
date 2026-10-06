"""
pages/5_Topup_Flaz.py — Analisis top up Flaz.
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

setup_anonim_page("Topup Flaz", "📦")
apply_theme()
apply_nav_style()
init_auth_state()

if not st.session_state.get("logged_in", False):
    st.warning("Silakan login dulu di halaman utama.")
    st.stop()

render_page_header(
    "Topup Flaz",
    "Analisis transaksi top up Flaz",
    icon="📦",
)

# ============================================================
# KONTEN
# ============================================================
if "db_path" not in st.session_state:
    st.warning("⚠️ Belum ada database. Upload dulu di Dashboard.")
    st.stop()

@st.cache_data(show_spinner=False)
def load_data(db_path):
    tables = ["tx_tsale", "tx_trans", "tx_trans_non_commerce"]
    return load_tables(db_path, tables)

try:
    dfs = load_data(st.session_state["db_path"])
    df_sale = dfs.get("tx_tsale", pd.DataFrame())
    df_nc = dfs.get("tx_trans_non_commerce", pd.DataFrame())
except Exception as e:
    st.error(f"Gagal load database: {e}")
    st.stop()

if df_sale.empty:
    st.info("Tabel tx_tsale kosong.")
    st.stop()

df_sale["date_tx"] = pd.to_datetime(df_sale["date_tx"], errors="coerce")
for c in ["total_faktur", "ol_payment", "wallet"]:
    if c in df_sale.columns:
        df_sale[c] = pd.to_numeric(df_sale[c], errors="coerce").fillna(0)

# Filter tanggal
render_section_title("Filter", "🔎")
if df_sale["date_tx"].notna().any():
    min_d = df_sale["date_tx"].min().date()
    max_d = df_sale["date_tx"].max().date()
    tgl_range = st.date_input(
        "Rentang Tanggal",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
        key="topup_tgl",
    )
    if len(tgl_range) == 2:
        mask = (
            (df_sale["date_tx"].dt.date >= tgl_range[0])
            & (df_sale["date_tx"].dt.date <= tgl_range[1])
        )
        df = df_sale[mask].copy()
    else:
        df = df_sale.copy()
else:
    df = df_sale.copy()

# Ringkasan
render_section_title("Ringkasan Topup", "📈")

total_omzet = df["total_faktur"].sum() if "total_faktur" in df.columns else 0
total_wallet = df["wallet"].sum() if "wallet" in df.columns else 0
total_ol = df["ol_payment"].sum() if "ol_payment" in df.columns else 0

metric_grid([
    {"label": "Total Omzet", "value": f"Rp {total_omzet:,.0f}", "variant": "accent"},
    {"label": "E-Wallet", "value": f"Rp {total_wallet:,.0f}", "variant": "success"},
    {"label": "Online Payment", "value": f"Rp {total_ol:,.0f}", "variant": "warning"},
], cols=3)

# Detail per kasir
render_section_title("Topup per Kasir", "👤")
if "user_id" in df.columns:
    per_kasir = (
        df.groupby("user_id")
        .agg(
            Total_Omzet=("total_faktur", "sum"),
            Total_Ewallet=("wallet", "sum"),
            Jumlah_Struk=("faktur", "nunique"),
        )
        .reset_index()
        .sort_values("Total_Omzet", ascending=False)
    )
    per_kasir.columns = ["NIK", "Omzet", "E-Wallet", "Jml Struk"]
    st.dataframe(per_kasir, use_container_width=True, hide_index=True)

    csv = per_kasir.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Topup per Kasir (CSV)",
        data=csv,
        file_name="topup_per_kasir.csv",
        mime="text/csv",
    )

render_footer()
