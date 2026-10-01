"""
2_SG_per_Paket.py — Laporan Serba Gratis per Paket (baca dari CSV).
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
from datetime import date

from utils.common import load_tables, normalize_plu_series
from utils.plu_dict import get_nama_plu
from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style
from utils.nav_helper import render_back_to_dashboard, safe_stop
from utils.plu_loader import load_plu_by_date, list_plu_files

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("2 SG per Paket", "🎁")
apply_nav_style()

st.title("🎁 Laporan Serba Gratis (SG) per Paket")
st.markdown("Menampilkan paket Serba Gratis berdasarkan periode (dari CSV).")

# ============================================================
# CEK DATABASE
# ============================================================
db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Dashboard dulu untuk upload ZIP.")
    safe_stop("sg")

st.success("Database: " + st.session_state.get("db_name", ""))

# ============================================================
# LOAD TABEL
# ============================================================
try:
    dfs = load_tables(db_file, ["tx_tsale", "tx_trans", "log_receipt_prn"])
    df_detail = dfs["tx_trans"]

    if df_detail.empty:
        st.error("Tabel tx_trans kosong.")
        safe_stop("sg")

    df_detail["date_tx"] = pd.to_datetime(df_detail["date_tx"], errors="coerce")

except Exception as e:
    st.error("Gagal load database: " + str(e))
    safe_stop("sg")

# ============================================================
# PILIH TANGGAL
# ============================================================
st.markdown("---")
st.markdown("### 📅 Pilih Tanggal")

if df_detail["date_tx"].notna().any():
    min_d = df_detail["date_tx"].min().date()
    max_d = df_detail["date_tx"].max().date()
    st.caption(f"Database: {min_d} s/d {max_d}")
    default_date = min_d
else:
    default_date = date.today()

tgl_pilih = st.date_input(
    "Tanggal analisis:",
    value=default_date,
    key="sg_tgl_pilih",
)

# Load PLU SG
plu_list, file_info = load_plu_by_date("sg", tgl_pilih)

if file_info is None:
    st.warning(f"⚠️ Tidak ada file PLU SG untuk tanggal **{tgl_pilih}**.")
    files = list_plu_files("sg")
    if files:
        with st.expander("📂 File PLU SG yang tersedia"):
            for f in files:
                st.write(f"- **{f['periode_label']}** → `{f['filename']}`")
    else:
        st.info("💡 Upload file di halaman **Manage PLU** → kategori **SG**.")
    safe_stop("sg")

st.success(f"✅ Periode: **{file_info['periode_label']}** — {len(plu_list)} PLU")

if not plu_list:
    st.warning("File PLU SG kosong.")
    safe_stop("sg")

# Bangun mapping PLU -> grup (dari kolom 'nama' atau 'mekanisme')
PLU_TO_GROUP = {}
for item in plu_list:
    plu = item["plu"]
    grup = item.get("nama", "") or item.get("mekanisme", "") or "SG"
    if grup not in PLU_TO_GROUP:
        PLU_TO_GROUP[grup] = []
    PLU_TO_GROUP[grup].append(plu)

ALL_PLU_SG = set([item["plu"] for item in plu_list])

# ============================================================
# FILTER & HITUNG
# ============================================================
st.markdown("---")

df_detail_temp = df_detail.copy()
df_detail_temp["plu_norm"] = normalize_plu_series(df_detail_temp["plu"], "buang_1")
df_detail_temp["plu_norm_int"] = df_detail_temp["plu_norm"].round().astype("Int64")

df_sg_all = df_detail_temp[
    df_detail_temp["plu_norm_int"].isin(ALL_PLU_SG)
].copy()

# Filter tanggal
df_sg_all = df_sg_all[df_sg_all["date_tx"].dt.date == tgl_pilih].copy()

st.info(f"Ditemukan **{len(df_sg_all)}** baris item SG di tanggal {tgl_pilih}.")

if df_sg_all.empty:
    st.warning("Tidak ada item SG di tanggal ini.")
    safe_stop("sg")

for c in ["qty", "price"]:
    if c in df_sg_all.columns:
        df_sg_all[c] = pd.to_numeric(df_sg_all[c], errors="coerce").fillna(0)

df_sg_all["bill_str"] = df_sg_all["bill_no"].astype(str).str.strip()

# ============================================================
# HITUNG PAKET (per struk per grup)
# ============================================================
paket_rows = []

for (bill, plu), grp in df_sg_all.groupby(["bill_str", "plu_norm_int"]):
    # Cari info grup
    grup_info = next((item for item in plu_list if item["plu"] == int(plu)), None)
    if not grup_info:
        continue

    nama_grup = grup_info.get("nama", "") or "SG"
    syarat_qty = grup_info.get("qty") or 3
    beli_qty = grup_info.get("beli_qty") or (syarat_qty - 1)

    total_qty = grp["qty"].sum()
    total_sales = (grp["price"] * grp["qty"]).sum()

    jumlah_paket = int(total_qty // syarat_qty)
    if jumlah_paket == 0:
        continue

    rasio_bayar = beli_qty / syarat_qty
    sales_bayar_per_paket = (total_sales / jumlah_paket) * rasio_bayar
    qty_per_paket = int(total_qty // jumlah_paket)

    for p in range(1, jumlah_paket + 1):
        paket_rows.append({
            "Faktur": bill,
            "Grup": nama_grup,
            "PLU": int(plu),
            "Nama_Item": get_nama_plu(int(plu)),
            "Jumlah_Paket": jumlah_paket,
            "Paket_Ke": p,
            "Qty_Paket": qty_per_paket,
            "Sales_Paket": sales_bayar_per_paket,
        })

df_paket = pd.DataFrame(paket_rows)

if df_paket.empty:
    st.warning("Tidak ada paket SG yang memenuhi syarat.")
    safe_stop("sg")

# ============================================================
# KPI
# ============================================================
st.markdown("---")
st.markdown("### 📊 Ringkasan")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Paket", format(len(df_paket), ","))
c2.metric("Total Struk", format(df_paket["Faktur"].nunique(), ","))
c3.metric("Total Qty", format(int(df_paket["Qty_Paket"].sum()), ","))
c4.metric("Total Sales", "Rp " + format(df_paket["Sales_Paket"].sum(), ",.0f"))

# ============================================================
# TABEL
# ============================================================
st.markdown("---")
st.markdown("### 📋 Tabel Paket SG")

df_display = df_paket[["Faktur", "Grup", "PLU", "Paket_Ke", "Qty_Paket", "Sales_Paket"]].copy()
df_display["Sales_Paket"] = df_display["Sales_Paket"].apply(
    lambda x: "Rp " + format(x, ",.0f")
)
st.dataframe(df_display, use_container_width=True, hide_index=True)

# Download
st.download_button(
    "📥 Download Tabel SG per Paket (CSV)",
    data=df_paket.to_csv(index=False).encode("utf-8"),
    file_name=f"sg_{tgl_pilih}.csv",
    mime="text/csv",
)

# ============================================================
# TOMBOL
# ============================================================
render_nav_universal("sg")
render_back_to_dashboard("sg")
