import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from utils.common import (
    load_tables, normalize_plu_series, format_struk,
    render_struk_html, generate_pdf, render_print_button,
    get_struk_text, build_plu_name_dict,
)
from utils.plu_dict import get_nama_plu

from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style

setup_anonim_page("Cek Struk", "🧾")
apply_nav_style()

st.title("🎁 Laporan Suger per Item")
st.markdown("Menampilkan item Suger beserta qty, sales, dan nomor bon.")

# ============================================================
# DAFTAR PLU SUGER
# ============================================================
PLU_SUGER = {
    120333,  # PUCUK HARUM TEH PET 350ML
    407443,  # SOSRO TEH BOTOL TAWAR PET 350ML
    125338,  # ICHI OCHA GREEN TEA PET 350ML
    444255,  # ULTRA TEH KOTAK LECI TP 300ML
    444254,  # ULTRA TEH KOTAK MANGGA TP 300ML
    410515,  # ULTRA TEH KOTAK LEMON TP 300ML
    414351,  # KUN UHT CHOMALT TPK 100ML
}

SYARAT_MIN = 20000

# ============================================================
# AMBIL DB DARI SESSION STATE
# ============================================================
db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Home dulu untuk upload ZIP.")
    st.stop()

st.success("Database: " + st.session_state.get("db_name", ""))

# ============================================================
# MAIN
# ============================================================
try:
    dfs = load_tables(db_file, ["tx_tsale", "tx_trans", "log_receipt_prn"])
    df_sale = dfs.get("tx_tsale", pd.DataFrame())
    df_detail = dfs.get("tx_trans", pd.DataFrame())
    df_receipt = dfs.get("log_receipt_prn", pd.DataFrame())

    if df_sale.empty:
        st.error("Tabel tx_tsale kosong.")
        st.stop()

    if df_detail.empty:
        st.error("Tabel tx_trans kosong.")
        st.stop()

    # ============================================================
    # NORMALISASI PLU
    # ============================================================
    df_detail["plu_asli"] = pd.to_numeric(df_detail["plu"], errors="coerce")

    # Coba beberapa mode normalisasi, pilih yang paling banyak match
    modes = ["asli", "buang_1", "buang_2", "div_10", "div_100"]
    best_mode = "buang_1"
    best_count = 0

    for mode in modes:
        df_temp = df_detail.copy()
        df_temp["_plu_norm"] = normalize_plu_series(df_temp["plu"], mode)
        df_temp["_plu_norm_int"] = df_temp["_plu_norm"].round().astype("Int64")
        cnt = int(df_temp["_plu_norm_int"].isin(PLU_SUGER).sum())
        if cnt > best_count:
            best_count = cnt
            best_mode = mode

    df_detail["plu_norm"] = normalize_plu_series(df_detail["plu"], best_mode)
    df_detail["plu_norm_int"] = df_detail["plu_norm"].round().astype("Int64")

    # Filter hanya PLU Suger
    df_suger_detail = df_detail[
        df_detail["plu_norm_int"].isin(PLU_SUGER)
    ].copy()

    st.caption(
        "Mode normalisasi PLU: **" + best_mode + "** — "
        "ditemukan **" + str(len(df_suger_detail)) + "** baris item Suger."
    )

    if df_suger_detail.empty:
        st.warning("Tidak ada item Suger di database ini.")
        st.stop()

    # Konversi numerik
    for c in ["qty", "price", "disc", "promo_disc"]:
        if c in df_suger_detail.columns:
            df_suger_detail[c] = pd.to_numeric(
                df_suger_detail[c], errors="coerce"
            ).fillna(0)

    df_suger_detail["bill_str"] = (
        df_suger_detail["bill_no"].astype(str).str.strip()
    )

    # ============================================================
    # FILTER STRUK SYARAT (total_belanja >= 20000)
    # ============================================================
    # Hitung total_belanja per faktur
    for c in ["total_faktur", "discount", "promo_disc"]:
        if c in df_sale.columns:
            df_sale[c] = pd.to_numeric(
                df_sale[c], errors="coerce"
            ).fillna(0)

    df_sale["total_belanja"] = (
        df_sale["total_faktur"]
        - df_sale["discount"]
        - df_sale["promo_disc"]
    )
    df_sale["is_syarat"] = df_sale["total_belanja"] >= SYARAT_MIN

    # ============================================================
    # KPI
    # ============================================================
    st.markdown("---")
    st.subheader("💰 Ringkasan Suger")

    # Total struk syarat
    total_struk = len(df_sale)
    total_struk_syarat = int(df_sale["is_syarat"].sum())

    # Total item Suger (baris)
    total_item_suger = len(df_suger_detail)

    # Total bon unik yang punya item Suger
    total_bon_suger = df_suger_detail["bill_str"].nunique()

    # Total sales item Suger (setelah diskon)
    total_sales_suger = (
        df_suger_detail["price"] * df_suger_detail["qty"]
        - df_suger_detail["promo_disc"]
    ).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🧾 Total Struk", format(total_struk, ","))
    c2.metric("✅ Struk Syarat", format(total_struk_syarat, ","))
    c3.metric("🎁 Bon dengan Item Suger", format(total_bon_suger, ","))
    c4.metric(
        "💵 Total Sales Suger",
        "Rp " + format(total_sales_suger, ",.0f")
    )

    # Info tambahan
    st.info(
        "Ditemukan " + str(total_item_suger) + " baris item Suger "
        "dari " + str(total_bon_suger) + " bon berbeda."
    )

    st.markdown("---")

    # ============================================================
    # AGREGASI PER PLU
    # ============================================================
    agg_rows = []
    for plu, grp in df_suger_detail.groupby("plu_norm_int"):
        plu_int = int(plu)

        qty = grp["qty"].sum()
        sales = (grp["price"] * grp["qty"]).sum()

        # Nama item
        plu_asli = grp["plu_asli"].iloc[0] if not grp.empty else plu_int
        nama = get_nama_plu(plu_asli)
        if nama == "-":
            nama = get_nama_plu(plu_int)

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

    st.markdown("### Tabel Suger per PLU")

    # Ringkasan tambahan
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Total PLU Suger", format(df_agg["PLU"].nunique(), ","))
    c6.metric("Total Qty", format(int(df_agg["Qty"].sum()), ","))
    c7.metric("Total Bon Unik", format(
        len(set(b for bl in df_agg["List_Bon"] for b in bl)), ","
    ))
    c8.metric(
        "Total Sales Item",
        "Rp " + format(df_agg["Sales_Item"].sum(), ",.0f")
    )

    st.markdown("---")

    # ============================================================
    # TAMPILKAN PER PLU
    # ============================================================
    for idx, row in df_agg.iterrows():
        plu = row["PLU"]
        nama = row["Nama_Item"]
        qty = row["Qty"]
        sales = row["Sales_Item"]
        list_bon = row["List_Bon"]
        jml_bon = row["Jumlah_Bon"]

        judul = (
            "PLU " + str(plu)
            + " - " + str(nama)
            + " - Qty: " + str(qty)
            + " - Sales: Rp " + format(sales, ",.0f")
            + " - " + str(jml_bon) + " bon"
        )

        with st.expander(judul):
            st.write("**Nama Item:** " + str(nama))
            st.write("**Total Qty:** " + str(qty))
            st.write("**Total Sales Item:** Rp " + format(sales, ",.0f"))
            st.write("**Jumlah Bon:** " + str(jml_bon))

            st.markdown("**Daftar Nomor Bon** (klik untuk lihat struk):")

            cols_per_row = 4
            for i in range(0, len(list_bon), cols_per_row):
                chunk = list_bon[i:i + cols_per_row]
                cols = st.columns(len(chunk))
                for col, bon in zip(cols, chunk):
                    btn_key = "suger_btn_" + str(plu) + "_" + str(bon)
                    if col.button(
                        "Bon " + str(bon),
                        key=btn_key,
                        use_container_width=True,
                    ):
                        st.session_state["suger_selected_bon"] = {
                            "plu": int(plu),
                            "bon": bon,
                        }

            sel = st.session_state.get("suger_selected_bon")
            if (sel
                    and sel["plu"] == int(plu)
                    and sel["bon"] in list_bon):

                st.markdown("---")
                st.markdown("### 🧾 Struk Bon " + str(sel["bon"]))

                struk_result = get_struk_text(df_receipt, sel["bon"])

                if struk_result and struk_result[0]:
                    full_receipt_text, raw_text = struk_result

                    receipt_html = render_struk_html(full_receipt_text)
                    components.html(receipt_html, height=650, scrolling=True)

                    st.write("")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.download_button(
                            label="📥 TXT",
                            data=full_receipt_text,
                            file_name="struk_bon_" + str(sel["bon"]) + ".txt",
                            mime="text/plain",
                            use_container_width=True,
                            key="suger_txt_" + str(plu) + "_" + str(sel["bon"]),
                        )

                    with col2:
                        try:
                            pdf_bytes = generate_pdf(full_receipt_text)
                            st.download_button(
                                label="📄 PDF",
                                data=pdf_bytes,
                                file_name="struk_bon_" + str(sel["bon"]) + ".pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="suger_pdf_" + str(plu) + "_" + str(sel["bon"]),
                            )
                        except ImportError:
                            st.info("Install `fpdf2` untuk PDF")
                        except Exception as e:
                            st.warning("PDF error: " + str(e))

                    with col3:
                        print_html = render_print_button(full_receipt_text)
                        with st.popover("🖨️ Cetak", use_container_width=True):
                            st.write("Klik tombol di bawah untuk print:")
                            components.html(print_html, height=80)

                    with st.expander("🔍 Lihat Teks Mentah (Debug)"):
                        st.code(raw_text, language=None)
                        st.write("**Setelah diformat:**")
                        st.code(full_receipt_text, language=None)

                else:
                    st.warning(
                        "Struk bon " + str(sel["bon"]) + " tidak ditemukan."
                    )

    st.markdown("---")

    # ============================================================
    # DOWNLOAD CSV
    # ============================================================
    df_export = df_agg.copy()
    df_export["List_Bon"] = df_export["List_Bon"].apply(
        lambda x: ", ".join(str(b) for b in x)
    )
    st.download_button(
        "📥 Download Tabel Suger per PLU (CSV)",
        data=df_export.to_csv(index=False).encode("utf-8"),
        file_name="suger_per_plu.csv",
        mime="text/csv",
    )

    # ============================================================
    # DEBUG
    # ============================================================
    with st.expander("🔍 Debug"):
        st.write("Total PLU Suger: " + str(len(PLU_SUGER)))
        st.write("Mode normalisasi: **" + best_mode + "**")
        st.write("Total baris item Suger: " + str(len(df_suger_detail)))
        st.write("Total bon dengan item Suger: " + str(total_bon_suger))
        st.write("Contoh PLU Suger di database:")
        st.write(df_suger_detail[["bill_no", "plu", "plu_norm_int", "price", "qty"]].head(10))

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)

render_nav_universal("struk")