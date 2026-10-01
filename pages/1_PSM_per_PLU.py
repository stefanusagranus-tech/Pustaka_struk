"""
1_PSM_per_PLU.py — Laporan PSM per PLU (baca dari file CSV).
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
from datetime import date

from utils.common import load_tables, detect_best_plu_mode
from utils.plu_dict import get_nama_plu, get_plu_normalized
from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style
from utils.nav_helper import render_back_to_dashboard, safe_stop
from utils.plu_loader import (
    list_plu_files,
    find_file_by_date,
    load_plu_by_date,
)

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("1 PSM per PLU", "📊")
apply_nav_style()

st.title("📦 Laporan PSM per PLU")
st.markdown("Menampilkan PLU PSM berdasarkan periode tanggal (dari file CSV).")

# ============================================================
# CEK DATABASE
# ============================================================
db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Dashboard dulu untuk upload ZIP.")
    safe_stop("psm")

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
        safe_stop("psm")

    if df_detail.empty:
        st.error("Tabel tx_trans kosong.")
        safe_stop("psm")

    df_detail["date_tx"] = pd.to_datetime(df_detail["date_tx"], errors="coerce")

except Exception as e:
    st.error("Gagal load database: " + str(e))
    safe_stop("psm")

# ============================================================
# PILIH TANGGAL → CARI FILE PLU
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
    key="psm_tgl_pilih",
)

# Cari file PLU
plu_list, file_info = load_plu_by_date(tgl_pilih)

if file_info is None:
    st.warning(f"⚠️ Tidak ada file PLU untuk tanggal **{tgl_pilih}**.")

    # Tampilkan file yang tersedia
    files = list_plu_files()
    if files:
        with st.expander("📂 File PLU yang tersedia"):
            for f in files:
                st.write(f"- **{f['periode_label']}** → `{f['filename']}`")
    else:
        st.info("💡 Belum ada file PLU. Buka halaman **Manage PLU** untuk upload.")

    safe_stop("psm")

st.success(
    f"✅ Periode: **{file_info['periode_label']}** — "
    f"{len(plu_list)} PLU"
)

if not plu_list:
    st.warning("File PLU kosong.")
    safe_stop("psm")

# Set PLU
PLU_PSM = set([item["plu"] for item in plu_list])

# ============================================================
# DETEKSI PLU
# ============================================================
st.markdown("---")

with st.spinner("Mendeteksi format PLU di database..."):
    best_mode, best_count, df_psm_detail = detect_best_plu_mode(
        df_detail, PLU_PSM
    )

st.info(f"Mode PLU: **{best_mode}** — ditemukan **{best_count}** baris item.")

if best_count == 0:
    st.warning("Tidak ada PLU PSM yang match dengan periode ini.")
    safe_stop("psm")

# ============================================================
# FILTER & AGREGASI
# ============================================================
for c in ["qty", "price", "disc", "promo_disc"]:
    if c in df_psm_detail.columns:
        df_psm_detail[c] = pd.to_numeric(
            df_psm_detail[c], errors="coerce"
        ).fillna(0)

# Filter tanggal
df_psm_detail = df_psm_detail[
    df_psm_detail["date_tx"].dt.date == tgl_pilih
].copy()

if df_psm_detail.empty:
    st.warning(f"Tidak ada transaksi PSM di tanggal {tgl_pilih}.")
    safe_stop("psm")

df_psm_detail["bill_str"] = df_psm_detail["bill_no"].astype(str).str.strip()

# Agregasi
agg_rows = []
for plu, grp in df_psm_detail.groupby("plu_norm_int"):
    plu_int = int(plu)
    plu_asli = grp["plu"].iloc[0]
    qty = grp["qty"].sum()
    sales = (grp["price"] * grp["qty"]).sum()
    list_bon = sorted(
        set(grp["bill_str"].unique()),
        key=lambda x: int(x) if x.isdigit() else 0
    )
    nama = get_nama_plu(plu_asli)

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
st.markdown("### 📊 Ringkasan PSM")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total PLU Aktif", format(df_agg["PLU"].nunique(), ","))
c2.metric("Total Qty", format(int(df_agg["Qty"].sum()), ","))
c3.metric("Total Bon Unik", format(
    len(set(b for bl in df_agg["List_Bon"] for b in bl)), ","
))
c4.metric("Total Sales", "Rp " + format(df_agg["Sales_Item"].sum(), ",.0f"))

# ============================================================
# TABEL
# ============================================================
st.markdown("---")
st.markdown("### 📋 Tabel PSM per PLU")

df_display = df_agg[["PLU", "Nama_Item", "Qty", "Sales_Item", "Jumlah_Bon"]].copy()
df_display["Sales_Item"] = df_display["Sales_Item"].apply(
    lambda x: "Rp " + format(x, ",.0f")
)
st.dataframe(df_display, use_container_width=True, hide_index=True)

# Detail per PLU
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
    "📥 Download Tabel PSM per PLU (CSV)",
    data=df_export.to_csv(index=False).encode("utf-8"),
    file_name=f"psm_{tgl_pilih}.csv",
    mime="text/csv",
)

# ============================================================
# TOMBOL
# ============================================================
render_nav_universal("psm")
render_back_to_dashboard("psm")
