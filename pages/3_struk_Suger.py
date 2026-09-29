import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from utils.common import (
    load_tables, normalize_plu_series,
    render_struk_html, generate_pdf, render_print_button,
    get_struk_text, build_plu_name_dict,
)
from utils.plu_dict import get_nama_plu, get_plu_normalized

st.set_page_config(
    page_title="Laporan Suger",
    page_icon="🎁",
    layout="wide",
)

st.title("🎁 Laporan Suger")
st.markdown("Analisis struk syarat Suger dan struk redeem.")

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
    # PREPARE DATA
    # ============================================================
    for c in ["total_faktur", "discount", "promo_disc", "wallet", "card", "cash"]:
        if c in df_sale.columns:
            df_sale[c] = pd.to_numeric(df_sale[c], errors="coerce").fillna(0)

    for c in ["price", "qty", "disc", "promo_disc"]:
        if c in df_detail.columns:
            df_detail[c] = pd.to_numeric(df_detail[c], errors="coerce").fillna(0)

    # Total belanja setelah diskon
    df_sale["total_belanja"] = (
        df_sale["total_faktur"]
        - df_sale["discount"]
        - df_sale["promo_disc"]
    )

    # Deteksi struk syarat
    df_sale["is_syarat"] = df_sale["total_belanja"] >= SYARAT_MIN

    # ============================================================
    # NORMALISASI PLU DI TX_TRANS
    # ============================================================
    df_detail["plu_asli"] = pd.to_numeric(df_detail["plu"], errors="coerce")

    # Coba semua mode normalisasi, pilih yang paling banyak match
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

    st.caption(
        "Mode normalisasi PLU terbaik: **" + best_mode + "** "
        "(ditemukan " + str(best_count) + " baris dengan PLU Suger)"
    )

    # Item Suger = PLU ada di daftar
    df_detail["is_suger_item"] = df_detail["plu_norm_int"].isin(PLU_SUGER)

    # Item redeem = PLU Suger DAN promo_disc > 0
    df_detail["is_redeem"] = (
        df_detail["is_suger_item"] & (df_detail["promo_disc"] > 0)
    )

    # Bill yang redeem (1 struk = 1 redeem)
    df_detail["bill_str"] = df_detail["bill_no"].astype(str).str.strip()
    bill_redeem_set = set(
        df_detail[df_detail["is_redeem"]]["bill_str"].unique()
    )

    # Tandai di tx_tsale (pakai faktur dulu, fallback ke bill_no)
    df_sale["bill_str"] = df_sale["faktur"].astype(str).str.strip()

    # Mapping faktur -> bill_no dari log_receipt_prn
    bill_to_no = {}
    if not df_receipt.empty and "bill_no" in df_receipt.columns:
        import re
        df_receipt_copy = df_receipt.copy()
        if "body1" in df_receipt_copy.columns:
            for _, r in df_receipt_copy.iterrows():
                b = str(r["bill_no"]).strip().zfill(4)
                body = str(r.get("body1", "")) + str(r.get("header", ""))
                m = re.search(r"C383-(\d+-\d+[A-Z0-9]+)", body)
                if m:
                    part = m.group(1)
                    if "-" in part:
                        faktur = "119-" + part.split("-", 1)[1]
                    else:
                        faktur = part
                    bill_to_no[faktur] = b

    # Tambahkan bill_no ke tx_tsale
    df_sale["bill_no"] = df_sale["faktur"].apply(
        lambda x: bill_to_no.get(str(x).strip(), "")
    )

    # Tandai redeem berdasarkan bill_no atau faktur
    df_sale["is_redeem"] = (
        df_sale["bill_no"].astype(str).isin(bill_redeem_set)
    )

    # Nama item per bill (untuk review)
    df_suger_items = df_detail[df_detail["is_suger_item"]].copy()

    if not df_suger_items.empty:
        df_suger_items["nama_item"] = df_suger_items["plu_asli"].apply(
            lambda x: get_nama_plu(x) if pd.notna(x) else "-"
        )

        suger_per_bill = (
            df_suger_items.groupby("bill_str")
            .agg(
                Item_Suger=("nama_item", lambda x: ", ".join(x.unique())),
                Jumlah_Item=("bill_str", "count"),
            )
            .to_dict("index")
        )
    else:
        suger_per_bill = {}

    df_sale["item_suger"] = df_sale["bill_no"].astype(str).apply(
        lambda x: suger_per_bill.get(x, {}).get("Item_Suger", "-")
    )

    # ============================================================
    # KPI
    # ============================================================
    st.markdown("---")
    st.subheader("💰 Ringkasan Suger")

    n_struk_total = len(df_sale)
    n_struk_syarat = int(df_sale["is_syarat"].sum())
    n_struk_redeem = int(df_sale["is_redeem"].sum())
    n_struk_syarat_no_redeem = n_struk_syarat - n_struk_redeem
    n_struk_tidak_syarat = n_struk_total - n_struk_syarat

    rasio_redeem = (
        (n_struk_redeem / n_struk_syarat * 100)
        if n_struk_syarat > 0 else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🧾 Total Struk", format(n_struk_total, ","))
    c2.metric("✅ Struk Syarat", format(n_struk_syarat, ","))
    c3.metric("🎁 Struk Redeem", format(n_struk_redeem, ","))
    c4.metric("📊 Rasio Redeem", format(rasio_redeem, ".1f") + "%")

    # ============================================================
    # PIE CHART
    # ============================================================
    st.markdown("---")
    st.subheader("📊 Diagram Struk")

    try:
        import plotly.graph_objects as go

        labels = [
            "Syarat + Redeem",
            "Syarat (Tidak Redeem)",
            "Tidak Syarat",
        ]
        values = [
            n_struk_redeem,
            n_struk_syarat_no_redeem,
            n_struk_tidak_syarat,
        ]
        colors = ["#2ecc71", "#f39c12", "#e74c3c"]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    marker=dict(colors=colors),
                    textinfo="label+percent+value",
                    textfont=dict(size=14),
                )
            ]
        )
        fig.update_layout(
            title="Distribusi Struk Suger",
            height=500,
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.warning("Install `plotly` di requirements.txt untuk pie chart.")

    # ============================================================
    # REVIEW STRUK
    # ============================================================
    st.markdown("---")
    st.subheader("📋 Review Struk")

    with st.expander("Filter", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            filter_status = st.multiselect(
                "Status:",
                options=["Syarat + Redeem", "Syarat (Tidak Redeem)", "Tidak Syarat"],
                default=["Syarat + Redeem", "Syarat (Tidak Redeem)", "Tidak Syarat"],
            )
        with col_b:
            sort_by = st.selectbox(
                "Urutkan:",
                ["Total Belanja (Desc)", "Total Belanja (Asc)", "Bill No"],
            )

    def get_status(row):
        if row["is_redeem"]:
            return "Syarat + Redeem"
        if row["is_syarat"]:
            return "Syarat (Tidak Redeem)"
        return "Tidak Syarat"

    df_sale["status"] = df_sale.apply(get_status, axis=1)
    df_review = df_sale[df_sale["status"].isin(filter_status)].copy()

    if sort_by == "Total Belanja (Desc)":
        df_review = df_review.sort_values("total_belanja", ascending=False)
    elif sort_by == "Total Belanja (Asc)":
        df_review = df_review.sort_values("total_belanja", ascending=True)
    else:
        df_review = df_review.sort_values("faktur", ascending=True)

    df_review = df_review.reset_index(drop=True)

    cols_show = [c for c in [
        "bill_no", "faktur", "date_tx", "time_tx", "user_id",
        "total_faktur", "discount", "promo_disc", "total_belanja",
        "status", "item_suger",
    ] if c in df_review.columns]

    df_display = df_review[cols_show].rename(columns={
        "bill_no": "Bill",
        "faktur": "Faktur",
        "date_tx": "Tanggal",
        "time_tx": "Jam",
        "user_id": "Kasir",
        "total_faktur": "Total Faktur",
        "discount": "Disc",
        "promo_disc": "Promo",
        "total_belanja": "Total Belanja",
        "status": "Status",
        "item_suger": "Item Suger",
    })

    for col in ["Total Faktur", "Disc", "Promo", "Total Belanja"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(
                lambda x: "Rp " + format(x, ",.0f")
            )

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    csv = df_review[cols_show].to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Review Suger (CSV)",
        data=csv,
        file_name="review_suger.csv",
        mime="text/csv",
    )

    # ============================================================
    # LIHAT STRUK
    # ============================================================
    st.markdown("---")
    st.subheader("🧾 Lihat Struk")

    # Pakai faktur (bukan bill_no) — karena bill_no mungkin kosong
    list_faktur = df_review["faktur"].dropna().unique().tolist()
    list_faktur = [f for f in list_faktur if str(f).strip() != ""]

    if list_faktur:
        selected_faktur = st.selectbox(
            "Pilih Faktur:",
            options=list_faktur,
            key="suger_faktur_select",
        )

        if selected_faktur:
            row = df_review[df_review["faktur"] == selected_faktur].iloc[0]

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Faktur", str(selected_faktur))
            col_b.metric(
                "Total Belanja",
                "Rp " + format(row["total_belanja"], ",.0f")
            )
            col_c.metric("Status", row["status"])

            # Cari bill_no dari log_receipt_prn (scan body1)
            bill_no = None
            if not df_receipt.empty and "bill_no" in df_receipt.columns:
                for _, r in df_receipt.iterrows():
                    body = str(r.get("body1", "")) + str(r.get("header", ""))
                    if str(selected_faktur) in body:
                        bill_no = str(r["bill_no"]).strip()
                        break

            if bill_no is None:
                # Fallback: coba dari faktur (ambil 3 digit terakhir)
                import re
                m = re.search(r"(\d+)$", str(selected_faktur))
                if m:
                    bill_no = m.group(1).lstrip("0")
                else:
                    bill_no = selected_faktur

            struk_result = get_struk_text(df_receipt, bill_no)

            if struk_result and struk_result[0]:
                full_receipt_text, raw_text = struk_result

                st.markdown("### Struk Faktur " + str(selected_faktur))
                receipt_html = render_struk_html(full_receipt_text)
                components.html(receipt_html, height=650, scrolling=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        "📥 TXT",
                        data=full_receipt_text,
                        file_name="struk_" + str(selected_faktur) + ".txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="suger_txt_" + str(selected_faktur),
                    )
                with col2:
                    try:
                        pdf_bytes = generate_pdf(full_receipt_text)
                        st.download_button(
                            "📄 PDF",
                            data=pdf_bytes,
                            file_name="struk_" + str(selected_faktur) + ".pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="suger_pdf_" + str(selected_faktur),
                        )
                    except ImportError:
                        st.info("Install fpdf2 untuk PDF")
                    except Exception as e:
                        st.warning("PDF error: " + str(e))
                with col3:
                    print_html = render_print_button(full_receipt_text)
                    with st.popover("🖨️ Cetak", use_container_width=True):
                        st.write("Klik tombol di bawah untuk print:")
                        components.html(print_html, height=80)
            else:
                st.warning("Struk tidak ditemukan untuk faktur " + str(selected_faktur))
    else:
        st.info("Tidak ada faktur di data review.")

    # ============================================================
    # DEBUG
    # ============================================================
    with st.expander("🔍 Debug"):
        st.write("Total PLU Suger: " + str(len(PLU_SUGER)))
        st.write("PLU Suger: " + str(sorted(list(PLU_SUGER))))
        st.write("Mode normalisasi PLU: **" + best_mode + "**")
        st.write("Baris Suger item (PLU match): " + str(df_detail["is_suger_item"].sum()))
        st.write("Baris redeem (PLU match + promo_disc > 0): " + str(df_detail["is_redeem"].sum()))
        st.write("Bill redeem: " + str(len(bill_redeem_set)))
        st.write("Contoh bill redeem: " + str(list(bill_redeem_set)[:10]))

        st.write("**10 baris tx_trans dengan PLU Suger:**")
        if df_detail["is_suger_item"].sum() > 0:
            df_sample = df_detail[df_detail["is_suger_item"]][
                ["bill_no", "plu", "plu_norm_int", "price", "qty", "promo_disc"]
            ].head(10)
            st.dataframe(df_sample, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)
