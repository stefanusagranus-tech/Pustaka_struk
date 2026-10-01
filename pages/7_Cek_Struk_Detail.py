"""
7_Cek_Struk_Detail.py
Search PLU atau Nomor Bon → tampil struk + list transaksi.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from utils.common import (
    load_tables,
    render_struk_html,
    generate_pdf,
    render_print_button,
    get_struk_text,
    build_plu_name_dict,
)
from utils.plu_dict import get_nama_plu, get_plu_normalized
from utils.anonim import setup_anonim_page, apply_nav_style

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("Cek Struk Detail", "🔍")
apply_nav_style()

st.title("🔍 Cek Struk Detail")
st.markdown("Search PLU atau Nomor Bon → lihat struk + rekap transaksi.")

# ============================================================
# CEK DATABASE
# ============================================================
db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Dashboard dulu untuk upload ZIP.")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🏠 Kembali ke Menu Utama", use_container_width=True, type="primary"):
            st.switch_page("App.py")
    st.stop()

st.success("Database aktif: " + st.session_state.get("db_name", ""))

# ============================================================
# LOAD TABEL
# ============================================================
@st.cache_data(show_spinner=False)
def load_all(db_path):
    tables = ["tx_tsale", "tx_trans", "log_receipt_prn"]
    return load_tables(db_path, tables)


try:
    dfs = load_all(db_file)
    df_sale = dfs.get("tx_tsale", pd.DataFrame())
    df_detail = dfs.get("tx_trans", pd.DataFrame())
    df_receipt = dfs.get("log_receipt_prn", pd.DataFrame())
except Exception as e:
    st.error("Gagal load database: " + str(e))
    st.stop()

if df_detail.empty:
    st.error("Tabel tx_trans kosong atau tidak ditemukan.")
    st.stop()

# ============================================================
# PREPARE DATA
# ============================================================
# Normalisasi PLU
if "plu" in df_detail.columns:
    df_detail["plu_str"] = df_detail["plu"].astype(str).str.strip()
    df_detail["plu_int"] = pd.to_numeric(
        df_detail["plu_str"], errors="coerce"
    ).fillna(0).astype(int)

# Normalisasi bill_no
if "bill_no" in df_detail.columns:
    df_detail["bill_str"] = df_detail["bill_no"].astype(str).str.strip()

# Normalisasi numerik
for c in ["qty", "price", "disc"]:
    if c in df_detail.columns:
        df_detail[c] = pd.to_numeric(df_detail[c], errors="coerce").fillna(0)

# Hitung total per baris
df_detail["total_row"] = df_detail["price"] * df_detail["qty"]
if "disc" in df_detail.columns:
    df_detail["total_row"] = df_detail["total_row"] - df_detail["disc"]

# ============================================================
# UI: FORM SEARCH
# ============================================================
st.markdown("---")
st.markdown("### 🔎 Search")

col_search, col_mode = st.columns([3, 1])

with col_mode:
    mode = st.selectbox(
        "Mode",
        ["PLU", "Nomor Bon"],
        key="search_mode",
    )

with col_search:
    if mode == "PLU":
        keyword = st.text_input(
            "Masukkan PLU",
            placeholder="Contoh: 435191",
            key="search_plu_input",
        )
    else:
        keyword = st.text_input(
            "Masukkan Nomor Bon",
            placeholder="Contoh: 149 atau 119-27090149",
            key="search_bon_input",
        )

btn_search = st.button("🔍 Cari", type="primary", use_container_width=True)

# ⬇️⬇️⬇️ LANJUT KE BAGIAN 2 ⬇️⬇️⬇️

# ============================================================
# LOGIC SEARCH
# ============================================================
if btn_search and keyword:
    keyword = str(keyword).strip()

    if mode == "PLU":
        # Search by PLU
        try:
            plu_target = int(keyword)
            df_result = df_detail[df_detail["plu_int"] == plu_target].copy()
        except ValueError:
            # Kalau bukan angka, coba exact match string
            df_result = df_detail[df_detail["plu_str"] == keyword].copy()

        search_label = f"PLU {keyword}"

    else:
        # Search by Nomor Bon
        # Nomor bon bisa "149" atau "119-27090149"
        # Normalisasi: buang leading zero, ambil 3 digit terakhir

        keyword_clean = keyword.replace("119-2709", "").replace("119-27090", "")
        keyword_clean = keyword_clean.strip()

        # Coba beberapa format
        if "-" in keyword:
            # Format "119-27090149"
            bill_part = keyword.split("-")[-1]
            bill_target = str(bill_part).strip()
        else:
            bill_target = keyword_clean

        # Cari di bill_str
        df_result = df_detail[
            df_detail["bill_str"].str.contains(bill_target, na=False)
        ].copy()

        search_label = f"Bon {keyword}"

    # ============================================================
    # HASIL SEARCH
    # ============================================================
    if df_result.empty:
        st.warning(f"❌ Tidak ada transaksi untuk **{search_label}**.")
        st.stop()

    st.success(f"✅ Ditemukan **{len(df_result)} baris** untuk **{search_label}**.")

    # ============================================================
    # DASHBOARD HASIL
    # ============================================================
    st.markdown("---")
    st.markdown("### 📊 Ringkasan Hasil")

    # KPI
    total_struk = df_result["bill_str"].nunique()
    total_sales = df_result["total_row"].sum()
    total_qty = df_result["qty"].sum()
    total_plu_unik = df_result["plu_int"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🧾 Jumlah Struk", format(int(total_struk), ","))
    c2.metric("📦 Total PLU Unik", format(int(total_plu_unik), ","))
    c3.metric("🔢 Total Qty", format(int(total_qty), ","))
    c4.metric("💰 Total Sales", "Rp " + format(total_sales, ",.0f"))

    # ============================================================
    # LIST PLU YANG MUNCUL
    # ============================================================
    st.markdown("---")
    st.markdown("### 📋 List PLU yang Muncul")

    plu_group = (
        df_result.groupby("plu_int")
        .agg(
            Nama_Item=("plu_int", lambda x: get_nama_plu(x.iloc[0])),
            Total_Qty=("qty", "sum"),
            Total_Sales=("total_row", "sum"),
            Jumlah_Transaksi=("bill_str", "nunique"),
        )
        .reset_index()
        .rename(columns={"plu_int": "PLU"})
        .sort_values("Total_Sales", ascending=False)
    )

    # Format
    plu_display = plu_group.copy()
    plu_display["Total_Sales"] = plu_display["Total_Sales"].apply(
        lambda x: "Rp " + format(x, ",.0f")
    )

    st.dataframe(plu_display, use_container_width=True, hide_index=True)

# ⬇️⬇️⬇️ LANJUT KE BAGIAN 3 ⬇️⬇️⬇️

    # ============================================================
    # LIST TRANSAKSI (per struk)
    # ============================================================
    st.markdown("---")
    st.markdown("### 📄 List Transaksi")

    # Group per struk
    struk_group = (
        df_result.groupby("bill_str")
        .agg(
            Jumlah_Item=("plu_int", "count"),
            Total_Qty=("qty", "sum"),
            Total_Sales=("total_row", "sum"),
        )
        .reset_index()
        .sort_values("Total_Sales", ascending=False)
    )

    # Tambahkan info kasir & waktu dari df_sale
    if not df_sale.empty and "faktur" in df_sale.columns:
        # Buat mapping bill_no -> info
        # bill_no di tx_trans = "149", faktur di tx_tsale = "119-27090149"
        df_sale_copy = df_sale.copy()
        df_sale_copy["bill_short"] = df_sale_copy["faktur"].astype(str).str.split("-").str[-1]

        bill_info = {}
        for _, r in df_sale_copy.iterrows():
            bill_short = str(r["bill_short"]).strip()
            bill_info[bill_short] = {
                "kasir": str(r.get("user_id", "-")),
                "waktu": str(r.get("time_tx", "-")),
                "faktur": str(r.get("faktur", "-")),
                "cust_id": str(r.get("cust_id", "-")),
            }

        struk_group["Kasir"] = struk_group["bill_str"].apply(
            lambda x: bill_info.get(str(x).strip(), {}).get("kasir", "-")
        )
        struk_group["Waktu"] = struk_group["bill_str"].apply(
            lambda x: bill_info.get(str(x).strip(), {}).get("waktu", "-")
        )
        struk_group["Faktur"] = struk_group["bill_str"].apply(
            lambda x: bill_info.get(str(x).strip(), {}).get("faktur", "-")
        )
    else:
        struk_group["Kasir"] = "-"
        struk_group["Waktu"] = "-"
        struk_group["Faktur"] = "-"

    # Tampilkan list struk
    st.markdown(f"**Total {len(struk_group)} struk**")

    for idx, row in struk_group.iterrows():
        bill = row["bill_str"]
        faktur = row["Faktur"]
        kasir = row["Kasir"]
        waktu = row["Waktu"]
        jml_item = row["Jumlah_Item"]
        total_qty = row["Total_Qty"]
        total_sales = row["Total_Sales"]

        # Header expander
        judul = (
            f"🧾 Bon {bill} | {waktu} | Kasir: {kasir} | "
            f"{jml_item} item | Rp {format(total_sales, ',.0f')}"
        )

        with st.expander(judul):
            # Info
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.write(f"**Nomor Bon:** {bill}")
                st.write(f"**Faktur:** {faktur}")
                st.write(f"**Kasir:** {kasir}")
            with col_i2:
                st.write(f"**Waktu:** {waktu}")
                st.write(f"**Jumlah Item:** {jml_item}")
                st.write(f"**Total Qty:** {int(total_qty)}")
                st.write(f"**Total Sales:** Rp {format(total_sales, ',.0f')}")

            # Detail item di struk ini
            st.markdown("**Detail Item:**")
            items_in_bill = df_result[df_result["bill_str"] == bill].copy()
            items_display = items_in_bill[["plu_int", "qty", "price", "disc", "total_row"]].copy()
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

            # Tombol lihat struk
            st.markdown("---")
            if st.button(f"📄 Lihat Struk Bon {bill}", key=f"btn_struk_{bill}_{idx}"):
                st.session_state["cek_struk_selected_bill"] = bill

            # Tampilkan struk kalau dipilih
            if st.session_state.get("cek_struk_selected_bill") == bill:
                st.markdown("---")
                st.markdown(f"### 📄 Struk Bon {bill}")

                struk_result = get_struk_text(df_receipt, bill)

                if struk_result and struk_result[0]:
                    full_receipt_text, raw_text = struk_result

                    # Render struk
                    receipt_html = render_struk_html(full_receipt_text)
                    components.html(receipt_html, height=650, scrolling=True)

                    st.write("")

                    # Tombol download
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

    # ============================================================
    # DOWNLOAD CSV
    # ============================================================
    st.markdown("---")

    csv_data = struk_group.copy()
    csv_data["Total_Sales"] = csv_data["Total_Sales"].apply(lambda x: f"{x:.0f}")
    st.download_button(
        "📥 Download List Transaksi (CSV)",
        data=csv_data.to_csv(index=False).encode("utf-8"),
        file_name=f"cek_struk_{keyword}.csv",
        mime="text/csv",
        use_container_width=True,
    )

elif btn_search and not keyword:
    st.warning("⚠️ Masukkan PLU atau Nomor Bon dulu.")

else:
    # Belum search
    st.info("💡 Masukkan PLU atau Nomor Bon di atas, lalu klik **🔍 Cari**.")

    # Info tambahan
    with st.expander("ℹ️ Cara Pakai"):
        st.markdown("""
        **Mode PLU:**
        - Masukkan PLU (contoh: `435191`)
        - Klik Cari
        - Muncul semua struk yang mengandung PLU tsb

        **Mode Nomor Bon:**
        - Masukkan nomor bon (contoh: `149` atau `119-27090149`)
        - Klik Cari
        - Muncul detail struk tersebut

        **Fitur:**
        - 📊 Ringkasan: jumlah struk, PLU unik, total sales
        - 📋 List PLU yang muncul di transaksi
        - 📄 List transaksi per struk
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
    if st.button("🏠 Kembali ke Menu Utama", use_container_width=True, key="back_to_menu_cek_struk"):
        st.switch_page("App.py")
