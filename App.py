
"""
App.py — Main app dengan login + menu pilih.
"""
import streamlit as st
import pandas as pd
import os
import shutil
from utils.common import (
    extract_zip_and_find_db,
    load_tables,
    build_kasir_dict_from_receipt,
)
from utils.anonim import setup_anonim_page, hide_only
from utils.auth import (
    init_auth_state,
    render_login_screen,
    render_menu_screen,
    render_back_to_menu_button,
    logout,
    back_to_menu,
)

# ============================================================
# SETUP HALAMAN
# ============================================================
setup_anonim_page("Pustaka Struk", "🏠")

# ============================================================
# INIT AUTH
# ============================================================
init_auth_state()


# ============================================================
# ROUTING
# ============================================================

# === 1. Belum login → tampilkan login ===
if not st.session_state.logged_in:
    render_login_screen()
    st.stop()

# === 2. Sudah login, belum pilih → tampilkan menu ===
if st.session_state.current_page is None:
    render_menu_screen()
    st.stop()

# === 3. Sudah pilih → render halaman ===

# --- Top bar ---
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    page_name = "📊 Dashboard" if st.session_state.current_page == "dashboard" else "💡 Idea Box"
    st.markdown(f"### {page_name}")
with col2:
    if st.button("⬅️ Menu", use_container_width=True, key="top_back"):
        back_to_menu()
with col3:
    if st.button("🚪 Logout", use_container_width=True, key="top_logout"):
        logout()

st.markdown("---")


# ============================================================
# HALAMAN: DASHBOARD
# ============================================================
if st.session_state.current_page == "dashboard":

    # ============================================================
    # UPLOAD DATABASE
    # ============================================================
    st.subheader("📁 Upload Database")

    uploaded_zip = st.file_uploader(
        "Upload file ZIP database",
        type=["zip"],
        key="main_zip_uploader",
    )

    extract_path = "temp_dashboard_db"

    if uploaded_zip is not None:
        with st.spinner("Mengekstrak & mencari database..."):
            db_path = extract_zip_and_find_db(uploaded_zip, extract_path)
        if db_path:
            st.session_state["db_path"] = db_path
            st.session_state["db_name"] = os.path.basename(db_path)
            st.success("Database berhasil dibaca: " + os.path.basename(db_path))
        else:
            st.error("Tidak ada file .db di dalam ZIP.")

    if "db_path" in st.session_state:
        st.info("Database aktif: " + st.session_state["db_name"])
        if st.button("Hapus database (reset)"):
            st.session_state.pop("db_path", None)
            st.session_state.pop("db_name", None)
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path, ignore_errors=True)
            st.rerun()
    else:
        st.warning("Belum ada database. Upload ZIP dulu di atas.")
        st.stop()

    st.markdown("---")

    # ============================================================
    # LOAD TABEL
    # ============================================================
    @st.cache_data(show_spinner=False)
    def get_data(db_path):
        tables = [
            "tx_tsale", "tx_tsale_card", "tx_trans",
            "log_receipt_prn", "tx_trans_non_commerce",
        ]
        return load_tables(db_path, tables)

    try:
        dfs = get_data(st.session_state["db_path"])
        df_sale = dfs.get("tx_tsale", pd.DataFrame())
        df_card = dfs.get("tx_tsale_card", pd.DataFrame())
        df_receipt = dfs.get("log_receipt_prn", pd.DataFrame())
        df_noncommerce = dfs.get("tx_trans_non_commerce", pd.DataFrame())
    except Exception as e:
        st.error("Gagal load database: " + str(e))
        st.stop()

    if df_sale.empty:
        st.error("Tabel tx_tsale kosong atau tidak ditemukan.")
        st.stop()

    kasir_dict = build_kasir_dict_from_receipt(df_receipt)

    # ============================================================
    # PREPARE DATA
    # ============================================================
    df_sale["date_tx"] = pd.to_datetime(df_sale["date_tx"], errors="coerce")

    num_cols = [
        "total_faktur", "cash", "card", "discount", "promo_disc",
        "charity", "cash_out", "wallet", "ol_payment", "voucher",
        "total_item",
    ]
    for c in num_cols:
        if c in df_sale.columns:
            df_sale[c] = pd.to_numeric(df_sale[c], errors="coerce").fillna(0)

    if not df_noncommerce.empty:
        if "date_tx" in df_noncommerce.columns:
            df_noncommerce["date_tx"] = pd.to_datetime(
                df_noncommerce["date_tx"], errors="coerce"
            )
        for c in ["price", "qty", "disc"]:
            if c in df_noncommerce.columns:
                df_noncommerce[c] = pd.to_numeric(
                    df_noncommerce[c], errors="coerce"
                ).fillna(0)

        df_noncommerce["total_bayar"] = (
            df_noncommerce["price"] * df_noncommerce["qty"]
        )
        if "disc" in df_noncommerce.columns:
            df_noncommerce["total_bayar"] -= df_noncommerce["disc"]

    # ============================================================
    # FILTER TANGGAL
    # ============================================================
    st.subheader("📅 Filter Tanggal")

    tgl_range = ()
    if df_sale["date_tx"].notna().any():
        min_d = df_sale["date_tx"].min().date()
        max_d = df_sale["date_tx"].max().date()
        tgl_range = st.date_input(
            "Rentang Tanggal",
            value=(min_d, max_d),
            min_value=min_d,
            max_value=max_d,
            key="dash_tgl",
        )
        if len(tgl_range) == 2:
            mask = (df_sale["date_tx"].dt.date >= tgl_range[0]) & (
                df_sale["date_tx"].dt.date <= tgl_range[1]
            )
            df = df_sale[mask].copy()
            if not df_noncommerce.empty and "date_tx" in df_noncommerce.columns:
                df_noncommerce = df_noncommerce[
                    (df_noncommerce["date_tx"].dt.date >= tgl_range[0])
                    & (df_noncommerce["date_tx"].dt.date <= tgl_range[1])
                ]
        else:
            df = df_sale.copy()
    else:
        df = df_sale.copy()

    st.caption("Menampilkan " + str(len(df)) + " transaksi.")

    # ============================================================
    # FUNGSI HITUNG CASH KLERK
    # ============================================================
    def hitung_cash_klerk(df_sub):
        def safe_sum(col):
            if col in df_sub.columns:
                return pd.to_numeric(df_sub[col], errors="coerce").fillna(0).sum()
            return 0.0
        return float(
            safe_sum("total_faktur") + safe_sum("charity")
            - safe_sum("discount") - safe_sum("card")
            - safe_sum("cash_out") - safe_sum("wallet")
            - safe_sum("ol_payment") - safe_sum("voucher")
        )

    # ============================================================
    # HITUNG NON-COMMERCE
    # ============================================================
    if not df_noncommerce.empty:
        total_noncommerce = df_noncommerce["total_bayar"].sum()
        total_trx_noncommerce = df_noncommerce["bill_no"].nunique()
    else:
        total_noncommerce = 0
        total_trx_noncommerce = 0

    noncommerce_per_kasir = {}
    if not df_noncommerce.empty and "user_id" in df_noncommerce.columns:
        nc_group = (
            df_noncommerce.groupby("user_id")
            .agg(Total_NC=("total_bayar", "sum"), Jumlah_NC=("bill_no", "nunique"))
            .reset_index()
        )
        for _, r in nc_group.iterrows():
            noncommerce_per_kasir[str(r["user_id"])] = {
                "total": r["Total_NC"],
                "jumlah": r["Jumlah_NC"],
            }

    # ============================================================
    # KPI UTAMA
    # ============================================================
    st.markdown("---")
    st.subheader("💰 Ringkasan Performa")

    total_omzet = df["total_faktur"].sum()
    total_struk = df["faktur"].nunique()
    total_cash_klerk = hitung_cash_klerk(df)

    total_omzet_reguler = total_omzet - total_noncommerce
    total_struk_reguler = total_struk - total_trx_noncommerce

    total_debit = 0
    if not df_card.empty and "amount" in df_card.columns:
        df_card_temp = df_card.copy()
        if "date_tx" in df_card_temp.columns:
            df_card_temp["date_tx"] = pd.to_datetime(
                df_card_temp["date_tx"], errors="coerce"
            )
            if len(tgl_range) == 2:
                df_card_temp = df_card_temp[
                    (df_card_temp["date_tx"].dt.date >= tgl_range[0])
                    & (df_card_temp["date_tx"].dt.date <= tgl_range[1])
                ]
        df_card_temp["amount"] = pd.to_numeric(
            df_card_temp["amount"], errors="coerce"
        ).fillna(0)
        total_debit = df_card_temp["amount"].sum()

    total_ewallet = df["wallet"].sum() if "wallet" in df.columns else 0

    if "cust_id" in df.columns:
        df["_is_member_kpi"] = df["cust_id"].apply(
            lambda x: str(x).strip() not in ["", "0", "0.0", "nan", "None"]
            and pd.notna(x)
        )
        total_sales_member = df[df["_is_member_kpi"]]["total_faktur"].sum()
    else:
        total_sales_member = 0

    total_item = df["total_item"].sum() if "total_item" in df.columns else 0

    st.markdown("##### 💰 Omzet")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Omzet Reguler", "Rp " + format(total_omzet_reguler, ",.0f"))
    c2.metric("📱 Omzet Non-Commerce", "Rp " + format(total_noncommerce, ",.0f"))
    c3.metric("📊 Total Omzet", "Rp " + format(total_omzet, ",.0f"))

    st.markdown("##### 🧾 Transaksi")
    c4, c5, c6 = st.columns(3)
    c4.metric("🧾 Total Struk Reguler", format(int(total_struk_reguler), ","))
    c5.metric("📱 Struk Non-Commerce", format(int(total_trx_noncommerce), ","))
    c6.metric("📦 Total Item", format(int(total_item), ","))

    st.markdown("##### 💳 Pembayaran")
    c7, c8, c9, c10 = st.columns(4)
    c7.metric("💵 Cash Klerk", "Rp " + format(total_cash_klerk, ",.0f"))
    c8.metric("💳 Total Debit", "Rp " + format(total_debit, ",.0f"))
    c9.metric("📱 Total E-Wallet", "Rp " + format(total_ewallet, ",.0f"))
    c10.metric("👥 Sales Member", "Rp " + format(total_sales_member, ",.0f"))

    # ============================================================
    # GRAFIK JAM RAMAI
    # ============================================================
    st.markdown("---")
    st.subheader("🕐 Jam Ramai Transaksi")

    if "time_tx" in df.columns and df["time_tx"].notna().any():
        df_time = df.copy()

        def get_hour(t):
            try:
                s = str(t).strip()
                if ":" in s:
                    return int(s.split(":")[0])
                return None
            except Exception:
                return None

        df_time["jam"] = df_time["time_tx"].apply(get_hour)
        df_time = df_time.dropna(subset=["jam"])
        df_time["jam"] = df_time["jam"].astype(int)

        if not df_time.empty:
            per_jam = (
                df_time.groupby("jam")["faktur"]
                .nunique()
                .reset_index()
                .rename(columns={"faktur": "Jumlah_Transaksi"})
            )
            all_hours = pd.DataFrame({"jam": range(24)})
            per_jam = all_hours.merge(per_jam, on="jam", how="left").fillna(0)
            per_jam["Jumlah_Transaksi"] = per_jam["Jumlah_Transaksi"].astype(int)

            chart_data = per_jam.set_index("jam")["Jumlah_Transaksi"]
            st.bar_chart(chart_data, use_container_width=True)
        else:
            st.info("Tidak ada transaksi di rentang tanggal ini.")
    else:
        st.info("Kolom time_tx tidak ditemukan.")

    # ============================================================
    # TABEL PER KASIR
    # ============================================================
    st.markdown("---")
    st.subheader("👤 Rekapitulasi per Kasir")

    if "user_id" in df.columns:
        if "cust_id" in df.columns:
            df["is_member"] = df["cust_id"].apply(
                lambda x: str(x).strip() not in ["", "0", "0.0", "nan", "None"]
                and pd.notna(x)
            )
        else:
            df["is_member"] = False

        agg_rows = []
        for kasir, grp in df.groupby("user_id"):
            sales_total = grp["total_faktur"].sum()
            nik_str = str(kasir)
            nc_data = noncommerce_per_kasir.get(nik_str, {"total": 0, "jumlah": 0})
            sales_nc = nc_data["total"]
            jumlah_nc = nc_data["jumlah"]
            sales_reguler = sales_total - sales_nc
            std_personil = grp["faktur"].nunique()
            std_reguler = std_personil - jumlah_nc
            grp_member = grp[grp["is_member"] == True]
            sales_member = grp_member["total_faktur"].sum() if not grp_member.empty else 0
            std_member = grp_member["faktur"].nunique() if not grp_member.empty else 0
            cash_klerk = hitung_cash_klerk(grp)
            ewallet_kasir = grp["wallet"].sum() if "wallet" in grp.columns else 0
            nama_kasir = kasir_dict.get(nik_str, "-")

            agg_rows.append({
                "NIK": nik_str,
                "Nama Kasir": nama_kasir,
                "Sales Reguler": sales_reguler,
                "Sales Non-Commerce": sales_nc,
                "STD Reguler": int(std_reguler),
                "Sales Member": sales_member,
                "Cash Klerk": cash_klerk,
                "E-Wallet": ewallet_kasir,
            })

        rekap_kasir = pd.DataFrame(agg_rows).sort_values(
            "Sales Reguler", ascending=False
        ).reset_index(drop=True)

        st.dataframe(rekap_kasir, use_container_width=True, hide_index=True)

        csv = rekap_kasir.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Rekap Kasir (CSV)",
            data=csv,
            file_name="rekap_kasir.csv",
            mime="text/csv",
        )


# ============================================================
# HALAMAN: IDEA BOX
# ============================================================
elif st.session_state.current_page == "idea_box":
    st.info("💡 Halaman Idea Box — paste kode dari `pages/0b_Idea_Box.py` di sini")
    st.markdown("Atau akses lewat menu sidebar kalau ada.")


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("Pustaka Struk v2.0 — Internal use only")
