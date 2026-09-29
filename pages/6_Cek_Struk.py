import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from utils.common import (
    load_tables,
    render_struk_html, generate_pdf, render_print_button,
    get_struk_text,
)

st.set_page_config(
    page_title="Cek Struk",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Cek Struk berdasarkan Flag")
st.markdown(
    "Menampilkan daftar bill_no dari `tx_trans` dengan filter **flag**, "
    "lalu tampilkan struk dari `log_receipt_prn`."
)

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
    dfs = load_tables(db_file, ["tx_trans", "log_receipt_prn"])
    df_trans = dfs.get("tx_trans", pd.DataFrame())
    df_receipt = dfs.get("log_receipt_prn", pd.DataFrame())

    if df_trans.empty:
        st.warning("Tabel tx_trans kosong.")
        st.stop()

    # ============================================================
    # FILTER FLAG
    # ============================================================
    st.subheader("🔍 Filter Flag")

    # Ambil semua nilai flag unik
    if "flag" in df_trans.columns:
        df_trans["flag_str"] = df_trans["flag"].astype(str).fillna("").str.strip()
        flag_unik = sorted(df_trans["flag_str"].unique().tolist())
    else:
        df_trans["flag_str"] = ""
        flag_unik = [""]

    st.write("Flag yang tersedia di database:")
    st.write(flag_unik)

    # Pilihan filter
    opsi_flag = st.multiselect(
        "Pilih flag (boleh pilih beberapa):",
        options=flag_unik,
        default=[f for f in flag_unik if f == ""] or flag_unik[:1],
    )

    if not opsi_flag:
        st.info("Pilih minimal 1 flag.")
        st.stop()

    # Filter
    df_filtered = df_trans[df_trans["flag_str"].isin(opsi_flag)].copy()

    st.caption(
        "Ditemukan **" + str(len(df_filtered)) + "** baris "
        + "dari **" + str(df_filtered["bill_no"].nunique()) + "** bill_no unik."
    )

    # ============================================================
    # DAFTAR BILL NO
    # ============================================================
    st.markdown("---")
    st.subheader("📋 Daftar Bill No")

    # Ambil bill_no unik
    if "bill_no" in df_filtered.columns:
        df_filtered["bill_no"] = pd.to_numeric(
            df_filtered["bill_no"], errors="coerce"
        )
        list_bill = sorted(
            df_filtered["bill_no"].dropna().unique().astype(int).tolist(),
            reverse=True,
        )
    else:
        st.error("Kolom bill_no tidak ditemukan di tx_trans.")
        st.stop()

    if not list_bill:
        st.warning("Tidak ada bill_no dengan flag yang dipilih.")
        st.stop()

    # ============================================================
    # PREVIEW DETAIL FLAG PER BILL
    # ============================================================
    with st.expander("📋 Lihat Detail Flag per Bill"):
        cols_detail = [c for c in [
            "bill_no", "plu", "qty", "price", "flag",
            "logpromo", "referensi",
        ] if c in df_filtered.columns]

        df_preview = df_filtered[cols_detail].sort_values(
            "bill_no", ascending=False
        ).reset_index(drop=True)

        st.dataframe(df_preview.head(200), use_container_width=True)
        if len(df_preview) > 200:
            st.caption("Menampilkan 200 baris pertama.")

    # ============================================================
    # PILIH BILL NO
    # ============================================================
    st.markdown("---")
    st.subheader("🧾 Lihat Struk")

    selected_bill = st.selectbox(
        "Pilih Bill No:",
        options=list_bill[:500],
        key="cek_struk_bill",
    )

    if selected_bill:
        # Info transaksi
        df_bill = df_filtered[df_filtered["bill_no"] == selected_bill]

        st.markdown("**Info Bill `" + str(selected_bill) + "`:**")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Jumlah Item", str(len(df_bill)))
        col_b.metric("Total Qty", str(int(df_bill["qty"].sum())))
        if "flag" in df_bill.columns:
            flag_vals = df_bill["flag"].astype(str).unique().tolist()
            col_c.metric("Flag", ", ".join(flag_vals) or "(kosong)")

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
                    key="cek_txt_" + str(selected_bill),
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
                        key="cek_pdf_" + str(selected_bill),
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

            # Debug teks mentah
            with st.expander("🔍 Lihat Teks Mentah (Debug)"):
                st.code(raw_text, language=None)
                st.write("**Setelah diformat:**")
                st.code(full_receipt_text, language=None)
        else:
            st.warning(
                "Struk bon " + str(selected_bill)
                + " tidak ditemukan di `log_receipt_prn`."
            )

        # Detail tx_trans untuk bill ini
        with st.expander("📋 Detail tx_trans untuk Bill ini"):
            cols_show = [c for c in [
                "bill_no", "user_id", "sort_no", "plu", "subdept",
                "price", "qty", "disc", "saving",
                "flag", "logpromo", "referensi", "type",
                "trans_time",
            ] if c in df_bill.columns]
            st.dataframe(df_bill[cols_show], use_container_width=True)

    # ============================================================
    # DEBUG
    # ============================================================
    with st.expander("🔍 Debug"):
        st.write("Total baris tx_trans: " + str(len(df_trans)))
        st.write("Total baris terfilter: " + str(len(df_filtered)))
        st.write("Distribusi flag:")
        if "flag_str" in df_trans.columns:
            dist_flag = df_trans["flag_str"].value_counts().reset_index()
            dist_flag.columns = ["Flag", "Jumlah"]
            st.dataframe(dist_flag, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)
