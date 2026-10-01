"""
2_SG_per_Paket.py — Laporan Serba Gratis per paket.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st

from utils.common import load_tables, normalize_plu_series
from utils.plu_dict import get_nama_plu
from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style
from utils.nav_helper import render_back_to_dashboard, safe_stop

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("2 SG per Paket", "🎁")
apply_nav_style()

st.title("🎁 Laporan Serba Gratis (SG) per Paket")
st.markdown("Menampilkan paket Serba Gratis yang sudah memenuhi syarat.")

# ============================================================
# KONFIGURASI GRUP SG
# ============================================================
SG_GROUPS = {
    "wow_spageti": {
        "plu": [444755, 444756, 448657, 461599],
        "nama": "WOW SPAGETI ALL VAR",
        "syarat_qty": 3, "beli_qty": 2,
    },
    "moms_recipe": {
        "plu": [441179, 110859],
        "nama": "MOM'S RECIPE SP TARO / MANGGA",
        "syarat_qty": 3, "beli_qty": 2,
    },
    "ramen_yes": {
        "plu": [453045, 453044],
        "nama": "RAMEN YES ALL VAR",
        "syarat_qty": 3, "beli_qty": 2,
    },
}

# Bangun mapping PLU -> grup
PLU_TO_GROUP = {}
for grp_key, grp_data in SG_GROUPS.items():
    for plu in grp_data["plu"]:
        PLU_TO_GROUP[plu] = grp_key

ALL_PLU_SG = set(PLU_TO_GROUP.keys())

# ============================================================
# CEK DATABASE
# ============================================================
db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Dashboard dulu untuk upload ZIP.")
    safe_stop("sg")

st.success("Database: " + st.session_state.get("db_name", ""))

# ============================================================
# MAIN
# ============================================================
try:
    dfs = load_tables(db_file, ["tx_tsale", "tx_trans", "log_receipt_prn"])
    df_detail = dfs["tx_trans"]

    if df_detail.empty:
        st.error("Tabel tx_trans kosong.")
        safe_stop("sg")

    # Filter PLU SG
    df_detail_temp = df_detail.copy()
    df_detail_temp["plu_norm"] = normalize_plu_series(df_detail_temp["plu"], "buang_1")
    df_detail_temp["plu_norm_int"] = df_detail_temp["plu_norm"].round().astype("Int64")

    df_sg_all = df_detail_temp[
        df_detail_temp["plu_norm_int"].isin(ALL_PLU_SG)
    ].copy()

    st.info("Ditemukan " + str(len(df_sg_all)) + " baris item dengan PLU SG.")

    if df_sg_all.empty:
        st.warning("Tidak ada item dengan PLU SG di database.")
        safe_stop("sg")

    for c in ["qty", "price"]:
        if c in df_sg_all.columns:
            df_sg_all[c] = pd.to_numeric(df_sg_all[c], errors="coerce").fillna(0)

    df_sg_all["grup"] = df_sg_all["plu_norm_int"].map(PLU_TO_GROUP)
    df_sg_all["bill_str"] = df_sg_all["bill_no"].astype(str).str.strip()

    # Hitung paket
    paket_rows = []
    for (bill, grup_key), grp in df_sg_all.groupby(["bill_str", "grup"]):
        grp_info = SG_GROUPS.get(grup_key)
        if grp_info is None:
            continue

        syarat_qty = grp_info["syarat_qty"]
        beli_qty = grp_info["beli_qty"]
        nama_grup = grp_info["nama"]

        total_qty = grp["qty"].sum()
        total_sales = (grp["price"] * grp["qty"]).sum()

        jumlah_paket = int(total_qty // syarat_qty)
        if jumlah_paket == 0:
            continue

        rasio_bayar = beli_qty / syarat_qty
        sales_per_paket = total_sales / jumlah_paket
        sales_bayar_per_paket = sales_per_paket * rasio_bayar
        qty_per_paket = int(total_qty // jumlah_paket)

        list_plu = sorted(grp["plu_norm_int"].unique().astype(int).tolist())
        nama_items = []
        for plu in list_plu:
            nm = get_nama_plu(plu)
            if nm != "-":
                nama_items.append(nm)
        nama_items_str = " + ".join(nama_items[:3])

        for p in range(1, jumlah_paket + 1):
            paket_rows.append({
                "Faktur": bill,
                "Grup": grup_key,
                "Nama_Grup": nama_grup,
                "PLU": list_plu,
                "Nama_Item": nama_items_str,
                "Jumlah_Paket": jumlah_paket,
                "Paket_Ke": p,
                "Qty_Paket": qty_per_paket,
                "Sales_Paket": sales_bayar_per_paket,
            })

    df_paket = pd.DataFrame(paket_rows)

    if df_paket.empty:
        st.warning("Tidak ada paket SG yang memenuhi syarat.")
        safe_stop("sg")

    # KPI
    st.markdown("### Tabel Paket Serba Gratis")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Paket", format(len(df_paket), ","))
    c2.metric("Total Struk", format(df_paket["Faktur"].nunique(), ","))
    c3.metric("Total Qty", format(int(df_paket["Qty_Paket"].sum()), ","))
    c4.metric("Total Sales", "Rp " + format(df_paket["Sales_Paket"].sum(), ",.0f"))

    st.markdown("---")

    # Tabel
    df_display = df_paket[["Faktur", "Nama_Grup", "Paket_Ke", "Qty_Paket", "Sales_Paket"]].copy()
    df_display["Sales_Paket"] = df_display["Sales_Paket"].apply(
        lambda x: "Rp " + format(x, ",.0f")
    )
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Download
    df_export = df_paket.copy()
    df_export["PLU"] = df_export["PLU"].apply(
        lambda x: ", ".join(str(p) for p in x) if isinstance(x, list) else x
    )
    st.download_button(
        "📥 Download Tabel SG per Paket (CSV)",
        data=df_export.to_csv(index=False).encode("utf-8"),
        file_name="sg_per_paket.csv",
        mime="text/csv",
    )

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)
    safe_stop("sg")

# ============================================================
# TOMBOL BAWAH
# ============================================================
render_nav_universal("sg")
render_back_to_dashboard("sg")