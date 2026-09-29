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
from utils.plu_dict import get_nama_plu, get_plu_normalized

st.set_page_config(
    page_title="PSM per PLU",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Laporan PSM per PLU")
st.markdown("Menampilkan PLU PSM beserta qty, sales, dan nomor bon.")

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
    df_sale = dfs["tx_tsale"]
    df_detail = dfs["tx_trans"]
    df_receipt = dfs["log_receipt_prn"]

    if df_sale.empty:
        st.error("Tabel tx_tsale kosong.")
        st.stop()

    if df_detail.empty:
        st.error("Tabel tx_trans kosong.")
        st.stop()

    # Auto-detect PLU
    with st.spinner("Mendeteksi format PLU di database..."):
        best_mode, best_count, df_psm_detail = detect_best_plu_mode(
            df_detail, PLU_PSM
        )

    st.info(
        "Mode PLU terbaik: " + best_mode
        + " — ditemukan " + str(best_count) + " baris item dengan PLU PSM."
    )

    with st.expander("Debug: Cek Format PLU", expanded=(best_count == 0)):
        st.write("PLU di database (20 contoh):")
        plu_sample = pd.to_numeric(df_detail["plu"], errors="coerce").dropna().astype(int).unique()
        st.write(sorted(list(plu_sample))[:20])
        st.write("Total PLU unik di database:", len(plu_sample))

        st.write("PLU PSM (20 contoh):")
        st.write(sorted(list(PLU_PSM))[:20])

        st.write("---")
        st.write("Hasil coba semua mode:")
        from utils.common import normalize_plu_series
        modes = ["asli", "buang_1", "buang_2", "div_10", "div_100"]
        hasil = []
        for mode in modes:
            df_temp = df_detail.copy()
            df_temp["plu_norm"] = normalize_plu_series(df_temp["plu"], mode)
            df_temp["plu_norm_int"] = df_temp["plu_norm"].round().astype("Int64")
            cnt = int(df_temp["plu_norm_int"].isin(PLU_PSM).sum())
            hasil.append({"mode": mode, "jumlah_match": cnt})
        st.dataframe(pd.DataFrame(hasil), use_container_width=True)

    if best_count == 0:
        st.warning("Tidak ada PLU PSM yang match. Cek debug di atas.")
        st.stop()

    for c in ["qty", "price", "disc", "promo_disc"]:
        if c in df_psm_detail.columns:
            df_psm_detail[c] = pd.to_numeric(
                df_psm_detail[c], errors="coerce"
            ).fillna(0)

    df_psm_detail["bill_str"] = df_psm_detail["bill_no"].astype(str).str.strip()

    plu_name_dict = build_plu_name_dict()

    st.success("Berhasil load " + str(len(plu_name_dict)) + " PLU dari dictionary.")

    st.success("Berhasil mapping " + str(len(plu_name_dict)) + " PLU ke nama.")

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
        plu_display = get_plu_normalized(plu_asli) or plu_int
    
        agg_rows.append({
            "PLU": plu_display,
            "Nama_Item": nama,
            "Qty": int(qty),
            "Sales_Item": sales,
            "List_Bon": list_bon,
            "Jumlah_Bon": len(list_bon),
        })

    df_agg = pd.DataFrame(agg_rows).sort_values(
        "Sales_Item", ascending=False
    ).reset_index(drop=True)

    st.markdown("### Tabel PSM per PLU")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total PLU", format(df_agg["PLU"].nunique(), ","))
    c2.metric("Total Qty", format(int(df_agg["Qty"].sum()), ","))
    c3.metric("Total Bon Unik", format(
        len(set(b for bl in df_agg["List_Bon"] for b in bl)), ","
    ))
    c4.metric("Total Sales Item", "Rp " + format(df_agg["Sales_Item"].sum(), ",.0f"))

    st.markdown("---")

    for idx, row in df_agg.iterrows():
        plu = row["PLU"]
        nama = row["Nama_Item"]
        qty = row["Qty"]
        sales = row["Sales_Item"]
        list_bon = row["List_Bon"]
        jml_bon = row["Jumlah_Bon"]

        judul = (
            "PLU " + str(plu) + " - " + str(nama)
            + " - Qty: " + str(qty)
            + " - Sales: Rp " + format(sales, ",.0f")
            + " - " + str(jml_bon) + " bon"
        )

        with st.expander(judul):
            st.write("Nama Item: " + str(nama))
            st.write("Total Qty: " + str(qty))
            st.write("Total Sales Item: Rp " + format(sales, ",.0f"))
            st.write("Jumlah Bon: " + str(jml_bon))

            st.markdown("Daftar Nomor Bon (klik untuk lihat struk):")

            cols_per_row = 4
            for i in range(0, len(list_bon), cols_per_row):
                chunk = list_bon[i:i + cols_per_row]
                cols = st.columns(len(chunk))
                for col, bon in zip(cols, chunk):
                    btn_key = "psm_btn_" + str(plu) + "_" + str(bon)
                    if col.button(
                        "Bon " + str(bon),
                        key=btn_key,
                        use_container_width=True,
                    ):
                        st.session_state["psm_selected_bon"] = {
                            "plu": int(plu),
                            "bon": bon,
                        }

            sel = st.session_state.get("psm_selected_bon")
            if (sel
                    and sel["plu"] == int(plu)
                    and sel["bon"] in list_bon):

                st.markdown("---")
                st.markdown("### Struk Bon " + str(sel["bon"]))

                struk_result = get_struk_text(df_receipt, sel["bon"])

                if struk_result and struk_result[0]:
                    full_receipt_text, raw_text = struk_result

                    receipt_html = render_struk_html(full_receipt_text)
                    components.html(receipt_html, height=650, scrolling=True)

                    st.write("")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.download_button(
                            label="TXT",
                            data=full_receipt_text,
                            file_name="struk_bon_" + str(sel["bon"]) + ".txt",
                            mime="text/plain",
                            use_container_width=True,
                            key="psm_txt_" + str(plu) + "_" + str(sel["bon"]),
                        )

                    with col2:
                        try:
                            pdf_bytes = generate_pdf(full_receipt_text)
                            st.download_button(
                                label="PDF",
                                data=pdf_bytes,
                                file_name="struk_bon_" + str(sel["bon"]) + ".pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="psm_pdf_" + str(plu) + "_" + str(sel["bon"]),
                            )
                        except ImportError:
                            st.info("Install fpdf2 untuk PDF")
                        except Exception as e:
                            st.warning("PDF error: " + str(e))

                    with col3:
                        print_html = render_print_button(full_receipt_text)
                        with st.popover("Cetak", use_container_width=True):
                            st.write("Klik tombol di bawah untuk print:")
                            components.html(print_html, height=80)

                    with st.expander("Lihat Teks Mentah (Debug)"):
                        st.code(raw_text, language=None)
                        st.write("Setelah diformat:")
                        st.code(full_receipt_text, language=None)

                else:
                    st.warning(
                        "Struk bon " + str(sel["bon"]) + " tidak ditemukan."
                    )

    st.markdown("---")

    df_export = df_agg.copy()
    df_export["List_Bon"] = df_export["List_Bon"].apply(
        lambda x: ", ".join(str(b) for b in x)
    )
    st.download_button(
        "Download Tabel PSM per PLU (CSV)",
        data=df_export.to_csv(index=False).encode("utf-8"),
        file_name="psm_per_plu.csv",
        mime="text/csv",
    )

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)
