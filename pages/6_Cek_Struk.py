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
    page_title="Void Transaksi",
    page_icon="🚫",
    layout="wide",
)

st.title("🚫 Laporan Void Transaksi")
st.markdown("Menampilkan transaksi yang dibatalkan (void) dari `tx_trans`.")

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
    dfs = load_tables(db_file, ["tx_trans", "tx_tsale", "log_receipt_prn"])
    df_trans = dfs.get("tx_trans", pd.DataFrame())
    df_sale = dfs.get("tx_tsale", pd.DataFrame())
    df_receipt = dfs.get("log_receipt_prn", pd.DataFrame())

    if df_trans.empty:
        st.warning("Tabel tx_trans kosong.")
        st.stop()

    # ============================================================
    # FILTER VOID (type = 'V')
    # ============================================================
    if "type" not in df_trans.columns:
        st.error("Kolom `type` tidak ditemukan di tx_trans.")
        st.stop()

    df_trans["type_str"] = df_trans["type"].astype(str).str.strip()
    df_void = df_trans[df_trans["type_str"] == "V"].copy()

    if df_void.empty:
        st.info("Tidak ada data void di database ini.")
        st.stop()

    # Konversi numerik
    for c in ["price", "qty", "disc"]:
        if c in df_void.columns:
            df_void[c] = pd.to_numeric(df_void[c], errors="coerce").fillna(0)

    # Nominal void = qty × price (qty negatif, jadi hasil negatif)
    df_void["nominal_void"] = df_void["qty"] * df_void["price"]

    # Ambil tanggal dari tx_tsale kalau ada
    if not df_sale.empty and "faktur" in df_sale.columns:
        # Mapping bill_no -> faktur & tanggal via log_receipt_prn
        pass  # nanti di bawah

    # ============================================================
    # MAPPING NAMA ITEM DARI STRUK
    # ============================================================
    with st.spinner("Membangun kamus nama item dari struk..."):
        plu_name_dict = build_plu_name_dict(df_receipt, df_trans)

    st.success(
        "Ditemukan " + str(len(df_void)) + " baris void "
        + "dari " + str(df_void["bill_no"].nunique()) + " transaksi."
    )

    # ============================================================
    # AMBIL TANGGAL & JAM DARI log_receipt_prn
    # ============================================================
    # mapping bill_no (4 digit) -> date_tx & trans_time
    bill_to_date = {}
    bill_to_faktur = {}

    if not df_receipt.empty and "bill_no" in df_receipt.columns:
        df_receipt_copy = df_receipt.copy()
        df_receipt_copy["_bill_z"] = (
            df_receipt_copy["bill_no"].astype(str).str.strip().str.zfill(4)
        )
        if "date_tx" in df_receipt_copy.columns:
            for _, r in df_receipt_copy.iterrows():
                b = str(r["bill_no"]).strip().zfill(4)
                bill_to_date[b] = r.get("date_tx", "")
        # Cari faktur di body1
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
                    bill_to_faktur[b] = faktur

    df_void["bill_str"] = df_void["bill_no"].astype(str).str.strip()
    df_void["bill_zfill"] = df_void["bill_str"].str.zfill(4)
    df_void["tanggal"] = df_void["bill_zfill"].apply(
        lambda x: bill_to_date.get(x, "")
    )
    df_void["faktur"] = df_void["bill_zfill"].apply(
        lambda x: bill_to_faktur.get(x, "")
    )

    # Nama item
    df_void["nama_item"] = df_void["plu"].apply(
        lambda x: plu_name_dict.get(int(float(x)), "-") if pd.notna(x) else "-"
    )

    # Jam void (dari trans_time)
    if "trans_time" not in df_void.columns:
        df_void["trans_time"] = ""

    # Supervisor (dari authorize)
    if "authorize" not in df_void.columns:
        df_void["authorize"] = ""

    # Urutkan: tanggal terbaru di atas
    df_void = df_void.sort_values(
        ["tanggal", "bill_zfill", "sort_no"],
        ascending=[False, False, True]
    ).reset_index(drop=True)
    # ============================================================
    # KPI
    # ============================================================
    st.markdown("---")
    st.subheader("💰 Ringkasan Void")

    total_void = df_void["bill_zfill"].nunique()
    total_nominal = df_void["nominal_void"].sum()
    total_qty = df_void["qty"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("🔢 Total Transaksi Void", format(total_void, ","))
    c2.metric("📦 Total Qty Void", format(int(total_qty), ","))
    c3.metric("💵 Total Nominal Void", "Rp " + format(total_nominal, ",.0f"))

    # ============================================================
    # FILTER & URUTKAN
    # ============================================================
    st.markdown("---")
    st.subheader("📋 Detail Void")

    with st.expander("Filter & Urutkan", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            sort_by = st.selectbox(
                "Urutkan berdasarkan:",
                ["Tanggal", "Nominal", "Bill No", "PLU"],
                index=0,
            )
        with col_b:
            sort_order = st.radio(
                "Urutan:", ["Descending", "Ascending"], horizontal=True
            )

        ascending = (sort_order == "Ascending")
        sort_map = {
            "Tanggal": "tanggal",
            "Nominal": "nominal_void",
            "Bill No": "bill_zfill",
            "PLU": "plu",
        }
        df_void = df_void.sort_values(
            sort_map.get(sort_by, "tanggal"),
            ascending=ascending
        ).reset_index(drop=True)

    # ============================================================
    # TABEL DETAIL
    # ============================================================
    cols_show = ["bill_zfill", "faktur", "tanggal", "trans_time",
                 "plu", "nama_item", "qty", "price", "nominal_void",
                 "authorize", "sort_no"]

    cols_show = [c for c in cols_show if c in df_void.columns]

    df_display = df_void[cols_show].copy()

    # Rename kolom
    df_display = df_display.rename(columns={
        "bill_zfill": "Bill No",
        "faktur": "Faktur",
        "tanggal": "Tanggal",
        "trans_time": "Jam",
        "plu": "PLU",
        "nama_item": "Nama Item",
        "qty": "Qty",
        "price": "Harga",
        "nominal_void": "Nominal Void",
        "authorize": "NIK Supervisor",
        "sort_no": "Sort",
    })

    # Format nominal & harga
    if "Nominal Void" in df_display.columns:
        df_display["Nominal Void"] = df_display["Nominal Void"].apply(
            lambda x: "Rp " + format(x, ",.0f")
        )
    if "Harga" in df_display.columns:
        df_display["Harga"] = df_display["Harga"].apply(
            lambda x: "Rp " + format(x, ",.0f")
        )

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # ============================================================
    # DOWNLOAD CSV
    # ============================================================
    csv = df_void[cols_show].to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Detail Void (CSV)",
        data=csv,
        file_name="detail_void.csv",
        mime="text/csv",
    )

    # ============================================================
    # LIHAT STRUK
    # ============================================================
    st.markdown("---")
    st.subheader("🧾 Lihat Struk Void")

    list_bill = sorted(
        df_void["bill_zfill"].dropna().unique().tolist(),
        reverse=True
    )

    if list_bill:
        selected_bill = st.selectbox(
            "Pilih Bill No:",
            options=list_bill,
            key="void_bill_select",
        )

        if selected_bill:
            # Info bill
            df_bill = df_void[df_void["bill_zfill"] == selected_bill]
            total_bill = df_bill["nominal_void"].sum()

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Bill No", str(selected_bill))
            col_b.metric("Jumlah Item Void", str(len(df_bill)))
            col_c.metric("Total Nominal Void", "Rp " + format(total_bill, ",.0f"))

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
                        file_name="struk_void_" + str(selected_bill) + ".txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="void_txt_" + str(selected_bill),
                    )
                with col2:
                    try:
                        pdf_bytes = generate_pdf(full_receipt_text)
                        st.download_button(
                            "📄 PDF",
                            data=pdf_bytes,
                            file_name="struk_void_" + str(selected_bill) + ".pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="void_pdf_" + str(selected_bill),
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
                st.warning(
                    "Struk bon " + str(selected_bill) + " tidak ditemukan."
                )

            # Detail item void
            with st.expander("📋 Detail Item Void untuk Bill Ini"):
                df_bill_show = df_bill[cols_show].rename(columns={
                    "bill_zfill": "Bill No",
                    "faktur": "Faktur",
                    "tanggal": "Tanggal",
                    "trans_time": "Jam",
                    "plu": "PLU",
                    "nama_item": "Nama Item",
                    "qty": "Qty",
                    "price": "Harga",
                    "nominal_void": "Nominal Void",
                    "authorize": "NIK Supervisor",
                    "sort_no": "Sort",
                })
                if "Nominal Void" in df_bill_show.columns:
                    df_bill_show["Nominal Void"] = df_bill_show["Nominal Void"].apply(
                        lambda x: "Rp " + format(x, ",.0f")
                    )
                if "Harga" in df_bill_show.columns:
                    df_bill_show["Harga"] = df_bill_show["Harga"].apply(
                        lambda x: "Rp " + format(x, ",.0f")
                    )
                st.dataframe(df_bill_show, use_container_width=True, hide_index=True)

    # ============================================================
    # DEBUG
    # ============================================================
    with st.expander("🔍 Debug"):
        st.write("Total baris tx_trans: " + str(len(df_trans)))
        st.write("Total baris void (type=V): " + str(len(df_void)))
        st.write("Jumlah bill void: " + str(df_void["bill_zfill"].nunique()))
        st.write("Kolom: ", df_trans.columns.tolist())

        # Distribusi type
        st.write("**Distribusi type di tx_trans:**")
        dist = df_trans["type_str"].value_counts().reset_index()
        dist.columns = ["Type", "Jumlah"]
        st.dataframe(dist, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)
