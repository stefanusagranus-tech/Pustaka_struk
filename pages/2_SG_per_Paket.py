"""
pages/2_SG_per_Paket.py — Analisis SG per Paket.
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

setup_anonim_page("SG per Paket", "🎁")
apply_theme()
apply_nav_style()
init_auth_state()

if not st.session_state.get("logged_in", False):
    st.warning("Silakan login dulu di halaman utama.")
    st.stop()

render_page_header(
    "SG per Paket",
    "Analisis penjualan SG (Serba Gratis) per paket",
    icon="🎁",
)

# ============================================================
# KONTEN
# ============================================================
if "db_path" not in st.session_state:
    st.warning("⚠️ Belum ada database. Upload dulu di Dashboard.")
    st.stop()

@st.cache_data(show_spinner=False)
def load_data(db_path):
    tables = ["tx_trans", "tx_tsale"]
    return load_tables(db_path, tables)

try:
    dfs = load_data(st.session_state["db_path"])
    df_trans = dfs.get("tx_trans", pd.DataFrame())
except Exception as e:
    st.error(f"Gagal load database: {e}")
    st.stop()

if df_trans.empty:
    st.info("Tabel tx_trans kosong.")
    st.stop()

df_trans["date_tx"] = pd.to_datetime(df_trans["date_tx"], errors="coerce")
for c in ["price", "qty", "disc"]:
    if c in df_trans.columns:
        df_trans[c] = pd.to_numeric(df_trans[c], errors="coerce").fillna(0)

# Filter tanggal
render_section_title("Filter", "🔎")
if df_trans["date_tx"].notna().any():
    min_d = df_trans["date_tx"].min().date()
    max_d = df_trans["date_tx"].max().date()
    tgl_range = st.date_input(
        "Rentang Tanggal",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
        key="sg_tgl",
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

# Filter SG (sesuaikan dengan logic SG kamu)
# Contoh: filter berdasarkan subdept atau flag tertentu
render_section_title("Ringkasan SG", "📈")

# Placeholder metric
metric_grid([
    {"label": "Total Paket", "value": "0", "variant": "accent"},
    {"label": "Total Qty", "value": "0"},
    {"label": "Total Omzet", "value": "Rp 0", "variant": "success"},
], cols=3)

# Placeholder tabel
render_section_title("Detail per Paket", "📋")
st.info("💡 Isi logic SG per paket di sini. Filter transaksi SG sesuai kode paket.")

# Contoh: group by kode paket (sesuaikan nama kolom)
if "promo_code" in df.columns:
    sg = (
        df[df["promo_code"].notna()]
        .groupby("promo_code")
        .agg(
            Total_Qty=("qty", "sum"),
            Total_Omzet=("price", lambda x: 0),
        )
        .reset_index()
    )
    st.dataframe(sg, use_container_width=True, hide_index=True)
else:
    st.caption("Kolom `promo_code` tidak ditemukan. Sesuaikan logic filter SG.")

render_footer()
