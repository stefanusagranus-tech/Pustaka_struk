"""
1_PSM_per_PLU.py — Laporan PSM per PLU.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from utils.common import (
    load_tables, detect_best_plu_mode,
    render_struk_html, generate_pdf, render_print_button,
    get_struk_text, build_plu_name_dict,
)
from utils.plu_dict import get_nama_plu, get_plu_normalized
from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style
from utils.nav_helper import render_back_to_dashboard, safe_stop

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("1 PSM per PLU", "📊")
apply_nav_style()

st.title("📦 Laporan PSM per PLU")
st.markdown("Menampilkan PLU PSM beserta qty, sales, dan nomor bon.")

# ============================================================
# DAFTAR PLU PSM
# ============================================================
PLU_PSM = {
    435191, 429397, 434880, 401632, 401633, 434281, 221623, 4504,
    4557, 118380, 118379, 440439, 461159, 5867, 5868, 401180,
    401181, 120076, 120077, 466031, 433323, 437941, 434243,
    434244, 432389, 444497, 451870, 451873, 451874, 124226,
    400443, 424005, 434414, 465935, 454047, 454048, 407263,
    418146, 413446, 440529, 450856, 425653, 452793, 119887,
    119895, 119898, 119899, 415150, 415376, 122157, 144353,
    428675, 428676, 431566, 428817, 428818, 453458, 453459,
}

# ============================================================
# CEK DATABASE
# ============================================================
db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Dashboard dulu untuk upload ZIP.")
    safe_stop("psm")

st.success("Database: " + st.session_state.get("db_name", ""))

# ============================================================
# MAIN
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

    # Auto-detect PLU
    with st.spinner("Mendeteksi format PLU di database..."):
        best_mode, best_count, df_psm_detail = detect_best_plu_mode(
            df_detail, PLU_PSM
        )

    st.info(
        "Mode PLU terbaik: " + best_mode
        + " — ditemukan " + str(best_count) + " baris item dengan PLU PSM."
    )

    if best_count == 0:
        st.warning("Tidak ada PLU PSM yang match.")
        safe_stop("psm")

    for c in ["qty", "price", "disc", "promo_disc"]:
        if c in df_psm_detail.columns:
            df_psm_detail[c] = pd.to_numeric(
                df_psm_detail[c], errors="coerce"
            ).fillna(0)

    df_psm_detail["bill_str"] = df_psm_detail["bill_no"].astype(str).str.strip()

    # Agregasi per PLU
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

    # KPI
    st.markdown("### Tabel PSM per PLU")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total PLU", format(df_agg["PLU"].nunique(), ","))
    c2.metric("Total Qty", format(int(df_agg["Qty"].sum()), ","))
    c3.metric("Total Bon Unik", format(
        len(set(b for bl in df_agg["List_Bon"] for b in bl)), ","
    ))
    c4.metric("Total Sales", "Rp " + format(df_agg["Sales_Item"].sum(), ",.0f"))

    st.markdown("---")

    # Tabel
    df_display = df_agg[["PLU", "Nama_Item", "Qty", "Sales_Item", "Jumlah_Bon"]].copy()
    df_display["Sales_Item"] = df_display["Sales_Item"].apply(
        lambda x: "Rp " + format(x, ",.0f")
    )
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Download
    df_export = df_agg.copy()
    df_export["List_Bon"] = df_export["List_Bon"].apply(
        lambda x: ", ".join(str(b) for b in x)
    )
    st.download_button(
        "📥 Download Tabel PSM per PLU (CSV)",
        data=df_export.to_csv(index=False).encode("utf-8"),
        file_name="psm_per_plu.csv",
        mime="text/csv",
    )

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)
    safe_stop("psm")

# ============================================================
# TOMBOL BAWAH
# ============================================================
render_nav_universal("psm")
render_back_to_dashboard("psm")