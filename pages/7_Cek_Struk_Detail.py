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
if "plu" in df_detail.columns:
    df_detail["plu_str"] = df_detail["plu"].astype(str).str.strip()
    df_detail["plu_int"] = pd.to_numeric(
        df_detail["plu_str"], errors="coerce"
    ).fillna(0).astype(int)

if "bill_no" in df_detail.columns:
    df_detail["bill_str"] = df_detail["bill_no"].astype(str).str.strip()

for c in ["qty", "price", "disc"]:
    if c in df_detail.columns:
        df_detail[c] = pd.to_numeric(df_detail[c], errors="coerce").fillna(0)

df_detail["total_row"] = df_detail["price"] * df_detail["qty"]
if "disc" in df_detail.columns:
    df_detail["total_row"] = df_detail["total_row"] - df_detail["disc"]

# ============================================================
# SESSION STATE
# ============================================================
if "cek_struk_search" not in st.session_state:
    st.session_state.cek_struk_search = {
        "mode": None,
        "keyword": None,
        "active": False,
    }

if "cek_struk_selected_bill" not in st.session_state:
    st.session_state.cek_struk_selected_bill = None

# ============================================================
# UI: FORM SEARCH
# ============================================================
st.markdown("---")
st.markdown("### 🔎 Search")

col_mode, col_keyword = st.columns([1, 3])

with col_mode:
    mode = st.selectbox(
        "Mode",
        ["PLU", "Nomor Bon"],
        key="search_mode_input",
    )

with col_keyword:
    if mode == "PLU":
        keyword = st.text_input(
            "Masukkan PLU (bisa sebagian)",
            placeholder="Contoh: 234 → muncul 2342, 23400, dll",
            key="search_plu_input",
        )
    else:
        keyword = st.text_input(
            "Masukkan Nomor Bon",
            placeholder="Contoh: 149 atau 119-27090149",
            key="search_bon_input",
        )

col_btn1, col_btn2 = st.columns([1, 1])

with col_btn1:
    btn_search = st.button("🔍 Cari", type="primary", use_container_width=True)

with col_btn2:
    btn_reset = st.button("🔄 Reset", use_container_width=True)

# ⬇️⬇️⬇️ LANJUT KE BAGIAN 2 ⬇️⬇️⬇️

# ============================================================
# HANDLE RESET
# ============================================================
if btn_reset:
    st.session_state.cek_struk_search = {
        "mode": None,
        "keyword": None,
        "active": False,
    }
    st.session_state.cek_struk_selected_bill = None
    st.rerun()

# ============================================================
# HANDLE SEARCH BUTTON
# ============================================================
if btn_search:
    if not keyword or not str(keyword).strip():
        st.warning("⚠️ Masukkan PLU atau Nomor Bon dulu.")
    else:
        st.session_state.cek_struk_search = {
            "mode": mode,
            "keyword": str(keyword).strip(),
            "active": True,
        }
        st.session_state.cek_struk_selected_bill = None

# ============================================================
# LOGIC SEARCH (baca dari session state)
# ============================================================
if st.session_state.cek_struk_search["active"]:
    mode = st.session_state.cek_struk_search["mode"]
    keyword = st.session_state.cek_struk_search["keyword"]

    # ============ SEARCH BY PLU (FLEKSIBEL) ============
    if mode == "PLU":
        keyword_clean = keyword.strip()

        # Coba konversi ke int
        try:
            plu_target = int(keyword_clean)
            keyword_int = plu_target
        except ValueError:
            plu_target = None
            keyword_int = None

        # Strategi search:
        # 1. Exact match (kalau keyword persis)
        # 2. Prefix match (kalau keyword cuma sebagian)
        # 3. Contains match (paling fleksibel)

        df_result = pd.DataFrame()

        if keyword_int is not None:
            keyword_str = str(keyword_int)

            # Cari PLU yang str-nya DIAWALI keyword
            df_detail["plu_str_full"] = df_detail["plu_int"].astype(str)
            df_result = df_detail[
                df_detail["plu_str_full"].str.startswith(keyword_str)
            ].copy()

            # Kalau hasil kosong, coba contains
            if df_result.empty:
                df_result = df_detail[
                    df_detail["plu_str_full"].str.contains(keyword_str, na=False)
                ].copy()
        else:
            # Kalau bukan angka, cari exact string
            df_result = df_detail[df_detail["plu_str"] == keyword_clean].copy()

        search_label = f"PLU {keyword}"

    # ============ SEARCH BY NOMOR BON ============
    else:
        if "-" in keyword:
            bill_part = keyword.split("-")[-1]
            bill_target = str(bill_part).strip()
        else:
            bill_target = keyword.strip()

        bill_target_clean = bill_target.lstrip("0") or "0"

        df_detail["bill_clean"] = (
            df_detail["bill_str"].astype(str).str.strip().str.lstrip("0")
        )

        df_result = df_detail[
            df_detail["bill_clean"] == bill_target_clean
        ].copy()

        search_label = f"Bon {keyword}"

    # ============================================================
    # HASIL SEARCH
    # ============================================================
    if df_result.empty:
        st.warning(f"❌ Tidak ada transaksi untuk **{search_label}**.")
        st.info("💡 Coba keyword lain atau reset pencarian.")

    else:
        st.success(f"✅ Ditemukan **{len(df_result)} baris** untuk **{search_label}**.")

        # ============================================================
        # DASHBOARD HASIL
        # ============================================================
        st.markdown("---")
        st.markdown("### 📊 Ringkasan Hasil")

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
                Total_Qty=("qty", "sum"),
                Total_Sales=("total_row", "sum"),
                Jumlah_Transaksi=("bill_str", "nunique"),
            )
            .reset_index()
            .rename(columns={"plu_int": "PLU"})
            .sort_values("Total_Sales", ascending=False)
        )

        plu_group["Nama_Item"] = plu_group["PLU"].apply(get_nama_plu)

        plu_display = plu_group[
            ["PLU", "Nama_Item", "Total_Qty", "Total_Sales", "Jumlah_Transaksi"]
        ].copy()
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

        # Info kasir & waktu dari df_sale
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
            struk_group["Kasir"] = "-"
            struk_group["Waktu"] = "-"
            struk_group["Faktur"] = "-"

        st.markdown(f"**Total {len(struk_group)} struk**")

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
                f"{jml_item} item | Rp {format(total_sales, ',.0f')}"
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
                    st.write(f"**Total Sales:** Rp {format(total_sales, ',.0f')}")

                st.markdown("**Detail Item:**")
                items_in_bill = df_result[df_result["bill_str"] == bill].copy()
                items_display = items_in_bill[
                    ["plu_int", "qty", "price", "disc", "total_row"]
                ].copy()
                items_display["Nama_Item"] = items_display["plu_int"].apply(get_nama_plu)
                items_display = items_display.rename(columns={
                    "plu_int": "PLU",
                    "qty": "Qty",
                    "price": "Harga",
                    "disc": "Disc",
                    "total_row": "Total",
                    "Nama_Item": "Nama",
                })
                st.dataframe(
                    items_display,
                    use_container_width=True,
                    hide_index=True,
                )

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

        # ============================================================
        # DOWNLOAD CSV
        # ============================================================
        st.markdown("---")

        csv_data = struk_group.drop(columns=["bill_clean"], errors="ignore").copy()
        csv_data["Total_Sales"] = csv_data["Total_Sales"].apply(lambda x: f"{x:.0f}")

        st.download_button(
            "📥 Download List Transaksi (CSV)",
            data=csv_data.to_csv(index=False).encode("utf-8"),
            file_name=f"cek_struk_{keyword}.csv",
            mime="text/csv",
            use_container_width=True,
        )

elif not st.session_state.cek_struk_search["active"]:
    # Belum search
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
        - 📋 List PLU yang muncul
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
    if st.button(
        "🏠 Kembali ke Menu Utama",
        use_container_width=True,
        key="back_to_menu_cek_struk",
    ):
        st.switch_page("App.py")
