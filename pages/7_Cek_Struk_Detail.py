"""
pages/7_Cek_Struk_Detail.py — Cek detail struk.
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

setup_anonim_page("Cek Struk Detail", "🔍")
apply_theme()
apply_nav_style()
init_auth_state()

if not st.session_state.get("logged_in", False):
    st.warning("Silakan login dulu di halaman utama.")
    st.stop()

render_page_header(
    "Cek Struk Detail",
    "Lihat detail lengkap sebuah transaksi",
    icon="🔍",
)

# ============================================================
# KONTEN
# ============================================================
if "db_path" not in st.session_state:
    st.warning("⚠️ Belum ada database. Upload dulu di Dashboard.")
    st.stop()

@st.cache_data(show_spinner=False)
def load_data(db_path):
    tables = ["tx_tsale", "tx_trans", "log_receipt_prn", "tx_tsale_card"]
    return load_tables(db_path, tables)

try:
    dfs = load_data(st.session_state["db_path"])
    df_sale = dfs.get("tx_tsale", pd.DataFrame())
    df_trans = dfs.get("tx_trans", pd.DataFrame())
    df_receipt = dfs.get("log_receipt_prn", pd.DataFrame())
    df_card = dfs.get("tx_tsale_card", pd.DataFrame())
except Exception as e:
    st.error(f"Gagal load database: {e}")
    st.stop()

# Input faktur
render_section_title("Cari Faktur", "🔎")
faktur_input = st.text_input(
    "Masukkan nomor faktur:",
    placeholder="Contoh: 119-27090149",
    key="detail_faktur",
)

if not faktur_input:
    st.info("Masukkan nomor faktur untuk melihat detail.")
    st.stop()

# ---- Header struk ----
sale = pd.DataFrame()
if not df_sale.empty and "faktur" in df_sale.columns:
    sale = df_sale[df_sale["faktur"].astype(str) == faktur_input.strip()]

if sale.empty:
    st.error(f"❌ Faktur `{faktur_input}` tidak ditemukan.")
    st.stop()

st.success(f"✅ Faktur ditemukan")

# ---- Info utama ----
render_section_title("Info Struk", "🧾")
row = sale.iloc[0]

metric_grid([
    {"label": "Faktur", "value": str(row.get("faktur", "-")), "variant": "accent"},
    {"label": "Tanggal", "value": str(row.get("date_tx", "-"))},
    {"label": "Jam", "value": str(row.get("time_tx", "-"))},
    {"label": "Kasir (NIK)", "value": str(row.get("user_id", "-"))},
], cols=4)

metric_grid([
    {"label": "Total Faktur", "value": f"Rp {float(row.get('total_faktur', 0) or 0):,.0f}", "variant": "success"},
    {"label": "Diskon", "value": f"Rp {float(row.get('discount', 0) or 0):,.0f}", "variant": "warning"},
    {"label": "Promo Disc", "value": f"Rp {float(row.get('promo_disc', 0) or 0):,.0f}", "variant": "warning"},
    {"label": "Cash", "value": f"Rp {float(row.get('cash', 0) or 0):,.0f}"},
], cols=4)

metric_grid([
    {"label": "Card", "value": f"Rp {float(row.get('card', 0) or 0):,.0f}"},
    {"label": "E-Wallet", "value": f"Rp {float(row.get('wallet', 0) or 0):,.0f}"},
    {"label": "Voucher", "value": f"Rp {float(row.get('voucher', 0) or 0):,.0f}"},
    {"label": "Online Payment", "value": f"Rp {float(row.get('ol_payment', 0) or 0):,.0f}"},
], cols=4)

# ---- Info Member ----
render_section_title("Info Member", "👤")
cust_id = row.get("cust_id", "")
if pd.notna(cust_id) and str(cust_id).strip() not in ["", "0", "0.0", "nan", "None"]:
    st.success(f"✅ Transaksi menggunakan member: **{cust_id}**")
else:
    st.info("ℹ️ Transaksi non-member (tidak pakai member).")

# ---- Detail item ----
render_section_title("Detail Item", "📦")
if not df_trans.empty and "bill_no" in df_trans.columns:
    bill_no = str(row.get("faktur", "")).split("-")[-1].lstrip("0")
    items = df_trans[df_trans["bill_no"].astype(str) == bill_no]
    if not items.empty:
        cols_show = [c for c in ["plu", "subdept", "price", "qty", "disc", "saving", "promo_code", "promo_no"] if c in items.columns]
        st.dataframe(items[cols_show], width="stretch", hide_index=True)
        csv = items.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Detail Item (CSV)",
            data=csv,
            file_name=f"detail_{faktur_input}.csv",
            mime="text/csv",
        )
    else:
        st.info("Tidak ada detail item di tx_trans.")

# ---- Struk ----
render_section_title("Struk", "🧾")
if not df_receipt.empty and "bill_no" in df_receipt.columns:
    bill_no_str = str(row.get("faktur", "")).split("-")[-1]
    receipt = df_receipt[df_receipt["bill_no"].astype(str) == bill_no_str.lstrip("0")]
    if not receipt.empty:
        r = receipt.iloc[0]
        for col in ["header", "body1", "body2", "body3", "addtl1", "addtl2", "addtl3", "footer"]:
            if col in receipt.columns and pd.notna(r.get(col)):
                st.text(str(r.get(col)))

# ---- Kartu ----
render_section_title("Kartu / Debit", "💳")
if not df_card.empty and "faktur" in df_card.columns:
    card = df_card[df_card["faktur"].astype(str) == faktur_input.strip()]
    if not card.empty:
        st.dataframe(card, width="stretch", hide_index=True)
    else:
        st.info("Tidak ada data kartu.")

# ============================================================
# NAVIGASI BAWAH
# ============================================================
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button(
        "🏠 Kembali ke Menu Utama",
        width="stretch",
        key="back_to_menu_detail",
    ):
        st.switch_page("App.py")

render_footer()
