"""
pages/7_Cek_Struk_Detail.py — Cek struk: cari faktur, cari struk, list & cetak.
"""
import os
import sys
from html import escape

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.anonim import setup_anonim_page, apply_nav_style
from utils.ui_theme import apply_theme
from utils.ui_components import (
    render_page_header,
    render_footer,
    render_section_title,
    metric_grid,
)
from utils.auth import init_auth_state
from utils.common import load_tables

# ------------------------------------------------------------------
# Helper functions — kalau sudah ada di utils/struk_utils.py, pakai itu.
# Kalau belum, fallback ini yang jalan.
# ------------------------------------------------------------------
try:
    from utils.struk_utils import (
        get_struk_text,
        render_struk_html,
        generate_pdf,
        render_print_button,
        get_nama_plu,
    )
except ImportError:
    # ---- Fallback minimal ----
    def get_nama_plu(plu):
        return f"PLU {plu}"

    def get_struk_text(df_receipt, bill):
        """Ambil teks struk dari df_receipt berdasarkan bill_no."""
        if df_receipt is None or df_receipt.empty:
            return None, None
        if "bill_no" not in df_receipt.columns:
            return None, None
        bill_clean = str(bill).lstrip("0") or "0"
        rows = df_receipt[df_receipt["bill_no"].astype(str).str.lstrip("0") == bill_clean]
        if rows.empty:
            return None, None
        r = rows.iloc[0]
        cols = ["header", "body1", "body2", "body3",
                "addtl1", "addtl2", "addtl3", "footer"]
        parts = [str(r.get(c, "")) for c in cols if pd.notna(r.get(c))]
        full_text = "\n".join(parts)
        return full_text, full_text

    def render_struk_html(text):
        return f"<pre style='font-family:monospace;font-size:12px'>{escape(text)}</pre>"

    def generate_pdf(text):
        try:
            from fpdf import FPDF
        except ImportError:
            raise ImportError("fpdf2 belum diinstall")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=9)
        for line in text.split("\n"):
            pdf.cell(0, 4, line, ln=1)
        return bytes(pdf.output(dest="S"))

    def render_print_button(text):
        safe = escape(text)
        return f"""
        <button onclick="window.print()" style="padding:8px 16px;font-size:14px;">
            🖨️ Print Struk
        </button>
        <pre style="display:none">{safe}</pre>
        """


# ============================================================
# SETUP HALAMAN
# ============================================================
setup_anonim_page("Cek Struk Detail", "🔍")
apply_theme()
apply_nav_style()
init_auth_state()

if not st.session_state.get("logged_in", False):
    st.warning("Silakan login dulu di halaman utama.")
    st.stop()

render_page_header(
    "Cek Struk Detail",
    "Cari struk, lihat detail, dan cetak",
    icon="🔍",
)

# ============================================================
# LOAD DATABASE
# ============================================================
if "db_path" not in st.session_state:
    st.warning("⚠️ Belum ada database. Upload dulu di Dashboard.")
    st.stop()


@st.cache_data(show_spinner=False)
def load_data(db_path):
    tables = ["tx_tsale", "tx_trans", "log_receipt_prn", "tx_tsale_card"]
    return load_tables(db_path, tables)


try:
    dfs = load_data(st.session_state["db_path"])
    df_sale = dfs.get("tx_tsale", pd.DataFrame())
    df_trans = dfs.get("tx_trans", pd.DataFrame())
    df_receipt = dfs.get("log_receipt_prn", pd.DataFrame())
    df_card = dfs.get("tx_tsale_card", pd.DataFrame())
except Exception as e:
    st.error(f"Gagal load database: {e}")
    st.stop()


# ============================================================
# SESSION STATE
# ============================================================
if "cek_struk_search" not in st.session_state:
    st.session_state.cek_struk_search = {"active": False, "keyword": "", "mode": ""}
if "cek_struk_selected_bill" not in st.session_state:
    st.session_state.cek_struk_selected_bill = None


# ============================================================
# TAB: 1) Cari Faktur  2) Cari Struk (PLU/Bon)
# ============================================================
tab_faktur, tab_struk = st.tabs(["🧾 Cek by Faktur", "🔎 Cari Struk (PLU/Bon)"])


# ============================================================
# TAB 1 — CEK BY FAKTUR
# ============================================================
with tab_faktur:
    render_section_title("Cari Faktur", "🔎")
    faktur_input = st.text_input(
        "Masukkan nomor faktur:",
        placeholder="Contoh: 119-27090149",
        key="detail_faktur",
    )

    if not faktur_input:
        st.info("Masukkan nomor faktur untuk melihat detail.")
    else:
        sale = pd.DataFrame()
        if not df_sale.empty and "faktur" in df_sale.columns:
            sale = df_sale[df_sale["faktur"].astype(str) == faktur_input.strip()]

        if sale.empty:
            st.error(f"❌ Faktur `{faktur_input}` tidak ditemukan.")
        else:
            st.success("✅ Faktur ditemukan")
            row = sale.iloc[0]

            # ---- Info Struk ----
            render_section_title("Info Struk", "🧾")
            metric_grid([
                {"label": "Faktur", "value": str(row.get("faktur", "-")), "variant": "accent"},
                {"label": "Tanggal", "value": str(row.get("date_tx", "-"))},
                {"label": "Jam", "value": str(row.get("time_tx", "-"))},
                {"label": "Kasir (NIK)", "value": str(row.get("user_id", "-"))},
            ], cols=4)

            metric_grid([
                {"label": "Total Faktur", "value": f"Rp {float(row.get('total_faktur', 0) or 0):,.0f}", "variant": "success"},
                {"label": "Diskon", "value": f"Rp {float(row.get('discount', 0) or 0):,.0f}", "variant": "warning"},
                {"label": "Promo Disc", "value": f"Rp {float(row.get('promo_disc', 0) or 0):,.0f}", "variant": "warning"},
                {"label": "Cash", "value": f"Rp {float(row.get('cash', 0) or 0):,.0f}"},
            ], cols=4)

            metric_grid([
                {"label": "Card", "value": f"Rp {float(row.get('card', 0) or 0):,.0f}"},
                {"label": "E-Wallet", "value": f"Rp {float(row.get('wallet', 0) or 0):,.0f}"},
                {"label": "Voucher", "value": f"Rp {float(row.get('voucher', 0) or 0):,.0f}"},
                {"label": "Online Payment", "value": f"Rp {float(row.get('ol_payment', 0) or 0):,.0f}"},
            ], cols=4)

            # ---- Info Member ----
            render_section_title("Info Member", "👤")
            cust_id = row.get("cust_id", "")
            if pd.notna(cust_id) and str(cust_id).strip() not in ["", "0", "0.0", "nan", "None"]:
                st.success(f"✅ Transaksi menggunakan member: **{cust_id}**")
            else:
                st.info("ℹ️ Transaksi non-member (tidak pakai member).")

            # ---- Detail Item ----
            render_section_title("Detail Item", "📦")
            if not df_trans.empty and "bill_no" in df_trans.columns:
                bill_no = str(row.get("faktur", "")).split("-")[-1].lstrip("0")
                items = df_trans[df_trans["bill_no"].astype(str).str.lstrip("0") == bill_no]
                if not items.empty:
                    cols_show = [c for c in ["plu", "subdept", "price", "qty",
                                             "disc", "saving", "promo_code",
                                             "promo_no"] if c in items.columns]
                    st.dataframe(items[cols_show], use_container_width=True, hide_index=True)
                    csv = items.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Download Detail Item (CSV)",
                        data=csv,
                        file_name=f"detail_{faktur_input}.csv",
                        mime="text/csv",
                    )
                else:
                    st.info("Tidak ada detail item di tx_trans.")

            # ---- Struk ----
            render_section_title("Struk", "🧾")
            if not df_receipt.empty and "bill_no" in df_receipt.columns:
                bill_no_str = str(row.get("faktur", "")).split("-")[-1].lstrip("0")
                receipt = df_receipt[df_receipt["bill_no"].astype(str).str.lstrip("0") == bill_no_str]
                if not receipt.empty:
                    r = receipt.iloc[0]
                    for col in ["header", "body1", "body2", "body3",
                                "addtl1", "addtl2", "addtl3", "footer"]:
                        if col in receipt.columns and pd.notna(r.get(col)):
                            st.text(str(r.get(col)))

            # ---- Kartu ----
            render_section_title("Kartu / Debit", "💳")
            if not df_card.empty and "faktur" in df_card.columns:
                card = df_card[df_card["faktur"].astype(str) == faktur_input.strip()]
                if not card.empty:
                    st.dataframe(card, use_container_width=True, hide_index=True)
                else:
                    st.info("Tidak ada data kartu.")


# ============================================================
# TAB 2 — CARI STRUK (PLU / NOMOR BON)
# ============================================================
with tab_struk:
    render_section_title("Cari Struk", "🔎")

    col1, col2 = st.columns([3, 1])
    with col1:
        keyword_input = st.text_input(
            "Masukkan PLU atau Nomor Bon:",
            placeholder="Contoh: 234  atau  149  atau  119-27090149",
            key="cek_struk_keyword",
        )
    with col2:
        st.write("")
        st.write("")
        do_search = st.button("🔍 Cari", use_container_width=True, key="btn_cek_struk_search")

    if do_search and keyword_input.strip():
        st.session_state.cek_struk_search = {
            "active": True,
            "keyword": keyword_input.strip(),
            "mode": "",
        }
        st.session_state.cek_struk_selected_bill = None

    search = st.session_state.cek_struk_search

    if search["active"] and search["keyword"]:
        keyword = search["keyword"]

        # ---- Persiapkan df_result ----
        if df_trans.empty:
            st.error("Tabel tx_trans kosong.")
            st.stop()

        df_result = df_trans.copy()

        # Normalisasi kolom
        if "bill_no" in df_result.columns:
            df_result["bill_str"] = df_result["bill_no"].astype(str).str.strip()
        elif "bill" in df_result.columns:
            df_result["bill_str"] = df_result["bill"].astype(str).str.strip()
        else:
            st.error("Kolom bill_no / bill tidak ditemukan di tx_trans.")
            st.stop()

        if "plu" in df_result.columns:
            df_result["plu_int"] = pd.to_numeric(df_result["plu"], errors="coerce")
        elif "plu_int" not in df_result.columns:
            df_result["plu_int"] = pd.NA

        # Hitung total_row kalau belum ada
        if "total_row" not in df_result.columns:
            price = pd.to_numeric(df_result.get("price", 0), errors="coerce").fillna(0)
            qty = pd.to_numeric(df_result.get("qty", 0), errors="coerce").fillna(0)
            disc = pd.to_numeric(df_result.get("disc", 0), errors="coerce").fillna(0)
            df_result["total_row"] = price * qty - disc

        for col in ["qty", "price", "disc"]:
            if col in df_result.columns:
                df_result[col] = pd.to_numeric(df_result[col], errors="coerce").fillna(0)

        # ---- Deteksi mode ----
        keyword_clean = keyword.strip().lstrip("0") or "0"
        is_bon_mode = keyword.replace("-", "").replace(" ", "").isdigit()

        if is_bon_mode:
            search["mode"] = "bon"
            # Kalau format 119-27090149, ambil bagian belakang
            if "-" in keyword:
                bill_part = keyword.split("-")[-1].lstrip("0")
            else:
                bill_part = keyword_clean
            df_filtered = df_result[
                df_result["bill_str"].astype(str).str.lstrip("0") == bill_part
            ]
        else:
            search["mode"] = "plu"
            # Cari PLU yang mengandung keyword
            df_filtered = df_result[
                df_result["plu_int"].astype(str).str.contains(keyword, na=False)
            ]

        if df_filtered.empty:
            st.warning(f"Tidak ada transaksi yang cocok dengan `{keyword}`.")
        else:
            # ---- Ringkasan ----
            render_section_title("Ringkasan", "📊")
            total_struk = df_filtered["bill_str"].nunique()
            total_plu = df_filtered["plu_int"].nunique()
            total_sales = df_filtered["total_row"].sum()
            total_qty = df_filtered["qty"].sum()

            metric_grid([
                {"label": "Jumlah Struk", "value": f"{total_struk}", "variant": "accent"},
                {"label": "PLU Unik", "value": f"{total_plu}"},
                {"label": "Total Qty", "value": f"{int(total_qty)}"},
                {"label": "Total Sales", "value": f"Rp {total_sales:,.0f}", "variant": "success"},
            ], cols=4)

            # ---- Group by bill ----
            struk_group = (
                df_filtered.groupby("bill_str")
                .agg(
                    Jumlah_Item=("plu_int", "count"),
                    Total_Qty=("qty", "sum"),
                    Total_Sales=("total_row", "sum"),
                )
                .reset_index()
                .sort_values("Total_Sales", ascending=False)
            )

            # ---- Info kasir & waktu dari df_sale ----
            if not df_sale.empty and "faktur" in df_sale.columns:
                df_sale_copy = df_sale.copy()
                df_sale_copy["bill_short"] = (
                    df_sale_copy["faktur"].astype(str).str.split("-").str[-1]
                )
                df_sale_copy["bill_short_clean"] = (
                    df_sale_copy["bill_short"].astype(str).str.strip().str.lstrip("0")
                )

                bill_info = {}
                for _, r in df_sale_copy.iterrows():
                    key = str(r["bill_short_clean"]).strip()
                    bill_info[key] = {
                        "kasir": str(r.get("user_id", "-")),
                        "waktu": str(r.get("time_tx", "-")),
                        "faktur": str(r.get("faktur", "-")),
                    }

                struk_group["bill_clean"] = (
                    struk_group["bill_str"].astype(str).str.strip().str.lstrip("0")
                )
                struk_group["Kasir"] = struk_group["bill_clean"].apply(
                    lambda x: bill_info.get(str(x).strip(), {}).get("kasir", "-")
                )
                struk_group["Waktu"] = struk_group["bill_clean"].apply(
                    lambda x: bill_info.get(str(x).strip(), {}).get("waktu", "-")
                )
                struk_group["Faktur"] = struk_group["bill_clean"].apply(
                    lambda x: bill_info.get(str(x).strip(), {}).get("faktur", "-")
                )
            else:
                struk_group["bill_clean"] = struk_group["bill_str"].astype(str).str.lstrip("0")
                struk_group["Kasir"] = "-"
                struk_group["Waktu"] = "-"
                struk_group["Faktur"] = "-"

            st.markdown(f"**Total {len(struk_group)} struk**")

            # ---- Loop struk ----
            for idx, row in struk_group.iterrows():
                bill = row["bill_str"]
                faktur = row["Faktur"]
                kasir = row["Kasir"]
                waktu = row["Waktu"]
                jml_item = row["Jumlah_Item"]
                total_qty = row["Total_Qty"]
                total_sales = row["Total_Sales"]

                judul = (
                    f"🧾 Bon {bill} | {waktu} | Kasir: {kasir} | "
                    f"{jml_item} item | Rp {total_sales:,.0f}"
                )

                with st.expander(judul):
                    col_i1, col_i2 = st.columns(2)
                    with col_i1:
                        st.write(f"**Nomor Bon:** {bill}")
                        st.write(f"**Faktur:** {faktur}")
                        st.write(f"**Kasir:** {kasir}")
                    with col_i2:
                        st.write(f"**Waktu:** {waktu}")
                        st.write(f"**Jumlah Item:** {jml_item}")
                        st.write(f"**Total Qty:** {int(total_qty)}")
                        st.write(f"**Total Sales:** Rp {total_sales:,.0f}")

                    st.markdown("**Detail Item:**")
                    items_in_bill = df_filtered[df_filtered["bill_str"] == bill].copy()
                    cols_item = [c for c in ["plu_int", "qty", "price", "disc", "total_row"] if c in items_in_bill.columns]
                    items_display = items_in_bill[cols_item].copy()
                    if "plu_int" in items_display.columns:
                        items_display["Nama_Item"] = items_display["plu_int"].apply(get_nama_plu)
                    items_display = items_display.rename(columns={
                        "plu_int": "PLU",
                        "qty": "Qty",
                        "price": "Harga",
                        "disc": "Disc",
                        "total_row": "Total",
                        "Nama_Item": "Nama",
                    })
                    st.dataframe(items_display, use_container_width=True, hide_index=True)

                    st.markdown("---")

                    # Tombol Lihat Struk
                    if st.button(
                        f"📄 Lihat Struk Bon {bill}",
                        key=f"btn_struk_{bill}_{idx}",
                    ):
                        st.session_state.cek_struk_selected_bill = bill
                        st.rerun()

                    # Tampilkan struk kalau dipilih
                    if st.session_state.cek_struk_selected_bill == bill:
                        st.markdown("---")
                        st.markdown(f"### 📄 Struk Bon {bill}")

                        struk_result = get_struk_text(df_receipt, bill)

                        if struk_result and struk_result[0]:
                            full_receipt_text, raw_text = struk_result

                            receipt_html = render_struk_html(full_receipt_text)
                            components.html(receipt_html, height=650, scrolling=True)

                            st.write("")

                            col_d1, col_d2, col_d3 = st.columns(3)

                            with col_d1:
                                st.download_button(
                                    "📥 TXT",
                                    data=full_receipt_text,
                                    file_name=f"struk_bon_{bill}.txt",
                                    mime="text/plain",
                                    use_container_width=True,
                                    key=f"txt_{bill}_{idx}",
                                )

                            with col_d2:
                                try:
                                    pdf_bytes = generate_pdf(full_receipt_text)
                                    st.download_button(
                                        "📥 PDF",
                                        data=pdf_bytes,
                                        file_name=f"struk_bon_{bill}.pdf",
                                        mime="application/pdf",
                                        use_container_width=True,
                                        key=f"pdf_{bill}_{idx}",
                                    )
                                except ImportError:
                                    st.info("Install fpdf2 untuk PDF")
                                except Exception as e:
                                    st.warning("PDF error: " + str(e))

                            with col_d3:
                                print_html = render_print_button(full_receipt_text)
                                with st.popover("🖨️ Cetak", use_container_width=True):
                                    st.write("Klik tombol di bawah untuk print:")
                                    components.html(print_html, height=80)

                            with st.expander("🔍 Lihat Teks Mentah (Debug)"):
                                st.code(raw_text, language=None)
                                st.write("Setelah diformat:")
                                st.code(full_receipt_text, language=None)
                        else:
                            st.warning(f"Struk bon {bill} tidak ditemukan di log_receipt_prn.")

            # ---- Download CSV ----
            st.markdown("---")
            csv_data = struk_group.drop(columns=["bill_clean"], errors="ignore").copy()
            if "Total_Sales" in csv_data.columns:
                csv_data["Total_Sales"] = csv_data["Total_Sales"].apply(lambda x: f"{x:.0f}")

            st.download_button(
                "📥 Download List Transaksi (CSV)",
                data=csv_data.to_csv(index=False).encode("utf-8"),
                file_name=f"cek_struk_{keyword}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    elif not search["active"]:
        st.info("💡 Masukkan PLU atau Nomor Bon di atas, lalu klik **🔍 Cari**.")

        with st.expander("ℹ️ Cara Pakai"):
            st.markdown("""
            **Mode PLU (fleksibel):**
            - Ketik `234` → muncul PLU `2342`, `23400`, `23421`, dll
            - Ketik `2342` → muncul PLU `2342` saja
            - Ketik `43` → muncul PLU `435191`, `434880`, dll

            **Mode Nomor Bon:**
            - Ketik `149` → muncul bon `149`
            - Ketik `119-27090149` → muncul bon `149`
            - Ketik `0149` → muncul bon `149`

            **Fitur:**
            - 📊 Ringkasan: jumlah struk, PLU unik, total sales
            - 📋 List transaksi per struk (expander)
            - 🔘 Tombol "Lihat Struk" untuk tampilkan struk
            - 📥 Download TXT / PDF
            - 🖨️ Cetak struk
            """)


# ============================================================
# NAVIGASI BAWAH
# ============================================================
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button(
        "🏠 Kembali ke Menu Utama",
        use_container_width=True,
        key="back_to_menu_cek_struk",
    ):
        st.switch_page("App.py")

render_footer()
        if df_filtered.empty:
            st.warning(f"Tidak ada transaksi yang cocok dengan `{keyword}`.")
        else:
            # ---- Ringkasan ----
            render_section_title("Ringkasan", "📊")
            total_struk = df_filtered["bill_str"].nunique()
            total_plu = df_filtered["plu_int"].nunique()
            total_sales = df_filtered["total_row"].sum()
            total_qty = df_filtered["qty"].sum()

            metric_grid([
                {"label": "Jumlah Struk", "value": f"{total_struk}", "variant": "accent"},
                {"label": "PLU Unik", "value": f"{total_plu}"},
                {"label": "Total Qty", "value": f"{int(total_qty)}"},
                {"label": "Total Sales", "value": f"Rp {total_sales:,.0f}", "variant": "success"},
            ], cols=4)

            # ---- Group by bill ----
            struk_group = (
                df_filtered.groupby("bill_str")
                .agg(
                    Jumlah_Item=("plu_int", "count"),
                    Total_Qty=("qty", "sum"),
                    Total_Sales=("total_row", "sum"),
                )
                .reset_index()
                .sort_values("Total_Sales", ascending=False)
            )

            # ---- Info kasir & waktu dari df_sale ----
            if not df_sale.empty and "faktur" in df_sale.columns:
                df_sale_copy = df_sale.copy()
                df_sale_copy["bill_short"] = (
                    df_sale_copy["faktur"].astype(str).str.split("-").str[-1]
                )
                df_sale_copy["bill_short_clean"] = (
                    df_sale_copy["bill_short"].astype(str).str.strip().str.lstrip("0")
                )

                bill_info = {}
                for _, r in df_sale_copy.iterrows():
                    key = str(r["bill_short_clean"]).strip()
                    bill_info[key] = {
                        "kasir": str(r.get("user_id", "-")),
                        "waktu": str(r.get("time_tx", "-")),
                        "faktur": str(r.get("faktur", "-")),
                    }

                struk_group["bill_clean"] = (
                    struk_group["bill_str"].astype(str).str.strip().str.lstrip("0")
                )
                struk_group["Kasir"] = struk_group["bill_clean"].apply(
                    lambda x: bill_info.get(str(x).strip(), {}).get("kasir", "-")
                )
                struk_group["Waktu"] = struk_group["bill_clean"].apply(
                    lambda x: bill_info.get(str(x).strip(), {}).get("waktu", "-")
                )
                struk_group["Faktur"] = struk_group["bill_clean"].apply(
                    lambda x: bill_info.get(str(x).strip(), {}).get("faktur", "-")
                )
            else:
                struk_group["bill_clean"] = struk_group["bill_str"].astype(str).str.lstrip("0")
                struk_group["Kasir"] = "-"
                struk_group["Waktu"] = "-"
                struk_group["Faktur"] = "-"

            st.markdown(f"**Total {len(struk_group)} struk**")

            # ---- Loop struk ----
            for idx, row in struk_group.iterrows():
                bill = row["bill_str"]
                faktur = row["Faktur"]
                kasir = row["Kasir"]
                waktu = row["Waktu"]
                jml_item = row["Jumlah_Item"]
                total_qty = row["Total_Qty"]
                total_sales = row["Total_Sales"]

                judul = (
                    f"🧾 Bon {bill} | {waktu} | Kasir: {kasir} | "
                    f"{jml_item} item | Rp {total_sales:,.0f}"
                )

                with st.expander(judul):
                    col_i1, col_i2 = st.columns(2)
                    with col_i1:
                        st.write(f"**Nomor Bon:** {bill}")
                        st.write(f"**Faktur:** {faktur}")
                        st.write(f"**Kasir:** {kasir}")
                    with col_i2:
                        st.write(f"**Waktu:** {waktu}")
                        st.write(f"**Jumlah Item:** {jml_item}")
                        st.write(f"**Total Qty:** {int(total_qty)}")
                        st.write(f"**Total Sales:** Rp {total_sales:,.0f}")

                    st.markdown("**Detail Item:**")
                    items_in_bill = df_filtered[df_filtered["bill_str"] == bill].copy()
                    cols_item = [c for c in ["plu_int", "qty", "price", "disc", "total_row"] if c in items_in_bill.columns]
                    items_display = items_in_bill[cols_item].copy()
                    if "plu_int" in items_display.columns:
                        items_display["Nama_Item"] = items_display["plu_int"].apply(get_nama_plu)
                    items_display = items_display.rename(columns={
                        "plu_int": "PLU",
                        "qty": "Qty",
                        "price": "Harga",
                        "disc": "Disc",
                        "total_row": "Total",
                        "Nama_Item": "Nama",
                    })
                    st.dataframe(items_display, use_container_width=True, hide_index=True)

                    st.markdown("---")

                    # Tombol Lihat Struk
                    if st.button(
                        f"📄 Lihat Struk Bon {bill}",
                        key=f"btn_struk_{bill}_{idx}",
                    ):
                        st.session_state.cek_struk_selected_bill = bill
                        st.rerun()

                    # Tampilkan struk kalau dipilih
                    if st.session_state.cek_struk_selected_bill == bill:
                        st.markdown("---")
                        st.markdown(f"### 📄 Struk Bon {bill}")

                        struk_result = get_struk_text(df_receipt, bill)

                        if struk_result and struk_result[0]:
                            full_receipt_text, raw_text = struk_result

                            receipt_html = render_struk_html(full_receipt_text)
                            components.html(receipt_html, height=650, scrolling=True)

                            st.write("")

                            col_d1, col_d2, col_d3 = st.columns(3)

                            with col_d1:
                                st.download_button(
                                    "📥 TXT",
                                    data=full_receipt_text,
                                    file_name=f"struk_bon_{bill}.txt",
                                    mime="text/plain",
                                    use_container_width=True,
                                    key=f"txt_{bill}_{idx}",
                                )

                            with col_d2:
                                try:
                                    pdf_bytes = generate_pdf(full_receipt_text)
                                    st.download_button(
                                        "📥 PDF",
                                        data=pdf_bytes,
                                        file_name=f"struk_bon_{bill}.pdf",
                                        mime="application/pdf",
                                        use_container_width=True,
                                        key=f"pdf_{bill}_{idx}",
                                    )
                                except ImportError:
                                    st.info("Install fpdf2 untuk PDF")
          
