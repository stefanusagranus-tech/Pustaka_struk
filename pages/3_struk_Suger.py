"""
3_struk_Suger.py — Laporan Suger per PLU (baca dari CSV).
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
setup_anonim_page("Laporan Suger", "🍬")
apply_nav_style()

st.title("🍬 Laporan Suger")
st.markdown("Menampilkan PLU Suger berdasarkan periode (dari CSV).")

# ============================================================
# CEK DATABASE
# ============================================================
db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Dashboard dulu untuk upload ZIP.")
    safe_stop("suger")

st.success("Database: " + st.session_state.get("db_name", ""))

# ============================================================
# LOAD TABEL
# ============================================================
try:
    dfs = load_tables(db_file, ["tx_tsale", "tx_trans", "log_receipt_prn"])
    df_sale = dfs["tx_tsale"]
    df_detail = dfs["tx_trans"]
    df_receipt = dfs["log_receipt_prn"]

    if df_sale.empty:
        st.error("Tabel tx_tsale kosong.")
        safe_stop("suger")

    if df_detail.empty:
        st.error("Tabel tx_trans kosong.")
        safe_stop("suger")

    df_detail["date_tx"] = pd.to_datetime(df_detail["date_tx"], errors="coerce")

except Exception as e:
    st.error("Gagal load database: " + str(e))
    safe_stop("suger")

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
    key="suger_tgl_pilih",
)

# Load PLU Suger
plu_list, file_info = load_plu_by_date("suger", tgl_pilih)

if file_info is None:
    st.warning(f"⚠️ Tidak ada file PLU Suger untuk tanggal **{tgl_pilih}**.")

    files = list_plu_files("suger")
    if files:
        with st.expander("📂 File PLU Suger yang tersedia"):
            for f in files:
                st.write(f"- **{f['periode_label']}** → `{f['filename']}`")
    else:
        st.info("💡 Upload file di halaman **Manage PLU** → kategori **Suger**.")

    safe_stop("suger")

st.success(f"✅ Periode: **{file_info['periode_label']}** — {len(plu_list)} PLU")

if not plu_list:
    st.warning("File PLU Suger kosong.")
    safe_stop("suger")

# Set PLU
PLU_SUGER = set([item["plu"] for item in plu_list])

# Mapping PLU → nama
PLU_NAMA = {}
for item in plu_list:
    nama_csv = item.get("nama", "")
    if not nama_csv:
        nama_csv = get_nama_plu(item["plu"])
    PLU_NAMA[item["plu"]] = nama_csv

# ============================================================
# FILTER & AGREGASI
# ============================================================
st.markdown("---")

df_detail_temp = df_detail.copy()
df_detail_temp["plu_norm"] = normalize_plu_series(df_detail_temp["plu"], "buang_1")
df_detail_temp["plu_norm_int"] = df_detail_temp["plu_norm"].round().astype("Int64")

df_suger = df_detail_temp[
    df_detail_temp["plu_norm_int"].isin(PLU_SUGER)
].copy()

# Filter tanggal
df_suger = df_suger[df_suger["date_tx"].dt.date == tgl_pilih].copy()

st.info(f"Ditemukan **{len(df_suger)}** baris item Suger di tanggal {tgl_pilih}.")

if df_suger.empty:
    st.warning("Tidak ada item Suger di tanggal ini.")
    safe_stop("suger")

# Normalisasi
for c in ["qty", "price", "disc"]:
    if c in df_suger.columns:
        df_suger[c] = pd.to_numeric(df_suger[c], errors="coerce").fillna(0)

df_suger["total_row"] = df_suger["price"] * df_suger["qty"]
if "disc" in df_suger.columns:
    df_suger["total_row"] = df_suger["total_row"] - df_suger["disc"]

df_suger["bill_str"] = df_suger["bill_no"].astype(str).str.strip()

# ============================================================
# AGREGASI PER PLU
# ============================================================
agg_rows = []
for plu, grp in df_suger.groupby("plu_norm_int"):
    plu_int = int(plu)
    nama = PLU_NAMA.get(plu_int, get_nama_plu(plu_int))
    qty = grp["qty"].sum()
    sales = grp["total_row"].sum()
    list_bon = sorted(
        set(grp["bill_str"].unique()),
        key=lambda x: int(x) if x.isdigit() else 0
    )

    agg_rows.append({
        "PLU": plu_int,
        "Nama_Item": nama,
        "Qty": int(qty),
        "Sales_Item": sales,
        "List_Bon": list_bon,
        "Jumlah_Bon": len(list_bon),
    })

df_agg = pd.DataFrame(agg_rows).sort_values(
    "Sales_Item", ascending=False
).reset_index(drop=True)

# ============================================================
# KPI
# ============================================================
st.markdown("---")
st.markdown("### 📊 Ringkasan Suger")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total PLU", format(df_agg["PLU"].nunique(), ","))
c2.metric("Total Qty", format(int(df_agg["Qty"].sum()), ","))
c3.metric("Total Bon Unik", format(
    len(set(b for bl in df_agg["List_Bon"] for b in bl)), ","
))
c4.metric("Total Sales", "Rp " + format(df_agg["Sales_Item"].sum(), ",.0f"))

# ============================================================
# TABEL
# ============================================================
st.markdown("---")
st.markdown("### 📋 Tabel Suger per PLU")

df_display = df_agg[["PLU", "Nama_Item", "Qty", "Sales_Item", "Jumlah_Bon"]].copy()
df_display["Sales_Item"] = df_display["Sales_Item"].apply(
    lambda x: "Rp " + format(x, ",.0f")
)
st.dataframe(df_display, use_container_width=True, hide_index=True)

# ============================================================
# DETAIL PER PLU
# ============================================================
st.markdown("---")
st.markdown("### 📂 Detail per PLU")

for idx, row in df_agg.iterrows():
    plu = row["PLU"]
    nama = row["Nama_Item"]
    qty = row["Qty"]
    sales = row["Sales_Item"]
    list_bon = row["List_Bon"]
    jml_bon = row["Jumlah_Bon"]

    judul = f"PLU {plu} - {nama} - Qty: {qty} - Rp {format(sales, ',.0f')} - {jml_bon} bon"

    with st.expander(judul):
        st.write(f"**Nama Item:** {nama}")
        st.write(f"**Total Qty:** {qty}")
        st.write(f"**Total Sales:** Rp {format(sales, ',.0f')}")
        st.write(f"**Jumlah Bon:** {jml_bon}")

        st.markdown("**Daftar Nomor Bon:**")
        cols_per_row = 4
        for i in range(0, min(len(list_bon), 20), cols_per_row):
            chunk = list_bon[i:i + cols_per_row]
            cols = st.columns(len(chunk))
            for col, bon in zip(cols, chunk):
                col.markdown(f"`Bon {bon}`")

        if len(list_bon) > 20:
            st.caption(f"... dan {len(list_bon) - 20} bon lainnya")

# ============================================================
# DOWNLOAD
# ============================================================
st.markdown("---")

df_export = df_agg.copy()
df_export["List_Bon"] = df_export["List_Bon"].apply(
    lambda x: ", ".join(str(b) for b in x)
)
st.download_button(
    "📥 Download Tabel Suger per PLU (CSV)",
    data=df_export.to_csv(index=False).encode("utf-8"),
    file_name=f"suger_{tgl_pilih}.csv",
    mime="text/csv",
)

# ============================================================
# TOMBOL
# ============================================================
render_nav_universal("struk")
render_back_to_dashboard("suger")
