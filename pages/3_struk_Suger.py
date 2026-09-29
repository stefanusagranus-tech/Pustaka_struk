import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from utils.common import (
    load_tables,
    render_struk_html, generate_pdf, render_print_button,
    get_struk_text, build_plu_name_dict,
)

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

    # Konversi numerik
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
    # DETEKSI REDEEM
    # ============================================================
    # PLU di tx_trans
    df_detail["plu_num"] = pd.to_numeric(df_detail["plu"], errors="coerce")

    # Item Suger = PLU ada di daftar DAN promo_disc > 0
    df_detail["is_suger_item"] = df_detail["plu_num"].isin(PLU_SUGER)
    df_detail["is_redeem"] = (
        df_detail["is_suger_item"] & (df_detail["promo_disc"] > 0)
    )

    # Bill yang redeem (1 struk = 1 redeem, ambil unik)
    df_detail["bill_str"] = df_detail["bill_no"].astype(str).str.strip()
    bill_redeem_set = set(
        df_detail[df_detail["is_redeem"]]["bill_str"].unique()
    )

    # Tandai di tx_tsale
    df_sale["bill_str"] = df_sale["faktur"].astype(str).str.strip()

    # Mapping bill_no dari log_receipt_prn
    bill_to_no = {}
    if not df_receipt.empty and "bill_no" in df_receipt.columns:
        df_receipt_copy = df_receipt.copy()
        if "body1" in df_receipt_copy.columns:
            import re
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

    # Map faktur -> bill_no
    df_sale["bill_no"] = df_sale["faktur"].apply(
        lambda x: bill_to_no.get(str(x).strip(), "")
    )

    # Tandai redeem berdasarkan bill_no
    df_sale["is_redeem"] = df_sale["bill_no"].astype(str).isin(bill_redeem_set)

    # Tambah nama item untuk review
    with st.spinner("Membangun kamus nama item..."):
        plu_name_dict = build_plu_name_dict(df_receipt, df_detail)

    # Item Suger per bill (untuk review)
    df_suger_items = df_detail[df_detail["is_redeem"]].copy()
    df_suger_items["nama_item"] = df_suger_items["plu_num"].apply(
        lambda x: plu_name_dict.get(int(x), "-") if pd.notna(x) else "-"
    )
    suger_per_bill = (
        df_suger_items.groupby("bill_str")
        .agg(
            Item_Suger=("nama_item", lambda x: ", ".join(x.unique())),
            Jumlah_Redeem=("bill_str", "count"),
        )
        .to_dict("index")
    )

    df_sale["item_suger"] = df_sale["bill_no"].astype(str).apply(
        lambda x: suger_per_bill.get(x, {}).get("Item_Suger", "-")
    )

    st.success(
        "Ditemukan " + str(len(df_sale)) + " struk total, "
        + str(df_sale["is_syarat"].sum()) + " syarat Suger, "
        + str(df_sale["is_redeem"].sum()) + " redeem."
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

    # ============================================================
    # REVIEW STRUK
    # ============================================================
    st.markdown("---")
    st.subheader("📋 Review Struk")

    # Filter
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

    # Tentukan status
    def get_status(row):
        if row["is_redeem"]:
            return "Syarat + Redeem"
        if row["is_syarat"]:
            return "Syarat (Tidak Redeem)"
        return "Tidak Syarat"

    df_sale["status"] = df_sale.apply(get_status, axis=1)
    df_review = df_sale[df_sale["status"].isin(filter_status)].copy()

    # Sort
    if sort_by == "Total Belanja (Desc)":
        df_review = df_review.sort_values("total_belanja", ascending=False)
    elif sort_by == "Total Belanja (Asc)":
        df_review = df_review.sort_values("total_belanja", ascending=True)
    else:
        df_review = df_review.sort_values("bill_no", ascending=True)

    df_review = df_review.reset_index(drop=True)

    # Tabel
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

    # Format rupiah
    for col in ["Total Faktur", "Disc", "Promo", "Total Belanja"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(
                lambda x: "Rp " + format(x, ",.0f")
            )

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Download CSV
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

    list_bill = df_review["bill_no"].dropna().unique().tolist()
    list_bill = [b for b in list_bill if str(b).strip() != ""]

    if list_bill:
        selected_bill = st.selectbox(
            "Pilih Bill:",
            options=list_bill,
            key="suger_bill_select",
        )

        if selected_bill:
            # Info bill
            row = df_review[df_review["bill_no"] == selected_bill].iloc[0]

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Bill No", str(selected_bill))
            col_b.metric(
                "Total Belanja",
                "Rp " + format(row["total_belanja"], ",.0f")
            )
            col_c.metric("Status", row["status"])

            # Tampilkan struk
            struk_result = get_struk_text(df_receipt, selected_bill)

            if struk_result and struk_result[0]:
                full_receipt_text, raw_text = struk_result

                st.markdown("### Struk Bon " + str(selected_bill))
                receipt_html = render_struk_html(full_receipt_text)
                components.html(receipt_html, height=650, scrolling=True)

                # Tombol aksi
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        "📥 TXT",
                        data=full_receipt_text,
                        file_name="struk_bon_" + str(selected_bill) + ".txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="suger_txt_" + str(selected_bill),
                    )
                with col2:
                    try:
                        pdf_bytes = generate_pdf(full_receipt_text)
                        st.download_button(
                            "📄 PDF",
                            data=pdf_bytes,
                            file_name="struk_bon_" + str(selected_bill) + ".pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="suger_pdf_" + str(selected_bill),
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
                st.warning("Struk tidak ditemukan untuk bill " + str(selected_bill))

    # ============================================================
    # DEBUG
    # ============================================================
    with st.expander("🔍 Debug"):
        st.write("Total PLU Suger: " + str(len(PLU_SUGER)))
        st.write("PLU Suger: " + str(sorted(list(PLU_SUGER))))
        st.write("Total baris tx_trans: " + str(len(df_detail)))
        st.write("Baris Suger item: " + str(df_detail["is_suger_item"].sum()))
        st.write("Baris redeem (promo_disc > 0): " + str(df_detail["is_redeem"].sum()))
        st.write("Bill redeem: " + str(len(bill_redeem_set)))
        st.write("Contoh bill redeem: " + str(list(bill_redeem_set)[:10]))

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)
