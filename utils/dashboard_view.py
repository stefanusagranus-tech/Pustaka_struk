"""
dashboard_view.py — Logic render Dashboard (dipisah dari App.py).
"""
import os
import re
import shutil

import pandas as pd
import streamlit as st

from utils.common import (
    extract_zip_and_find_db,
    load_tables,
    build_kasir_dict_from_receipt,
)
from utils.ui_components import (
    render_header,
    render_section_title,
    metric_grid,
    render_card,
)


# ============================================================
# Helper
# ============================================================
def _hitung_cash_klerk(df_sub: pd.DataFrame) -> float:
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


def _get_hour(t):
    try:
        s = str(t).strip()
        return int(s.split(":")[0]) if ":" in s else None
    except Exception:
        return None


# ============================================================
# Upload Section
# ============================================================
def render_upload_section():
    render_section_title("Upload Database", "📁")
    uploaded_zip = st.file_uploader(
        "Upload file ZIP database",
        type=["zip"],
        key="main_zip_uploader",
        label_visibility="collapsed",
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
        col_info, col_btn = st.columns([4, 1])
        with col_info:
            st.info("Database aktif: " + st.session_state["db_name"])
        with col_btn:
            if st.button("🗑️ Reset", use_container_width=True, key="reset_db"):
                st.session_state.pop("db_path", None)
                st.session_state.pop("db_name", None)
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path, ignore_errors=True)
                st.rerun()
        return True
    else:
        st.warning("Belum ada database. Upload ZIP dulu di atas.")
        return False


# ============================================================
# Load Data
# ============================================================
@st.cache_data(show_spinner=False)
def _load_data(db_path: str):
    tables = [
        "tx_tsale",
        "tx_tsale_card",
        "tx_trans",
        "log_receipt_prn",
        "tx_trans_non_commerce",
        "tx_usi",                       # ← untuk nama member
    ]
    return load_tables(db_path, tables)


def load_and_prepare():
    try:
        dfs = _load_data(st.session_state["db_path"])
        df_sale = dfs.get("tx_tsale", pd.DataFrame())
        df_card = dfs.get("tx_tsale_card", pd.DataFrame())
        df_receipt = dfs.get("log_receipt_prn", pd.DataFrame())
        df_noncommerce = dfs.get("tx_trans_non_commerce", pd.DataFrame())
        df_usi = dfs.get("tx_usi", pd.DataFrame())
    except Exception as e:
        st.error("Gagal load database: " + str(e))
        st.stop()

    if df_sale.empty:
        st.error("Tabel tx_tsale kosong atau tidak ditemukan.")
        st.stop()

    kasir_dict = build_kasir_dict_from_receipt(df_receipt)

    # Prepare tx_tsale
    df_sale["date_tx"] = pd.to_datetime(df_sale["date_tx"], errors="coerce")
    num_cols = [
        "total_faktur", "cash", "card", "discount", "promo_disc",
        "charity", "cash_out", "wallet", "ol_payment", "voucher", "total_item",
    ]
    for c in num_cols:
        if c in df_sale.columns:
            df_sale[c] = pd.to_numeric(df_sale[c], errors="coerce").fillna(0)

    # Prepare non-commerce
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

    return df_sale, df_card, df_receipt, df_noncommerce, df_usi, kasir_dict


# ============================================================
# Filter Tanggal
# ============================================================
def render_date_filter(df_sale: pd.DataFrame):
    render_section_title("Filter Tanggal", "📅")
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
            label_visibility="collapsed",
        )
    return tgl_range


def apply_filter(df_sale, df_noncommerce, tgl_range):
    if len(tgl_range) == 2:
        mask = (
            (df_sale["date_tx"].dt.date >= tgl_range[0])
            & (df_sale["date_tx"].dt.date <= tgl_range[1])
        )
        df = df_sale[mask].copy()
        if not df_noncommerce.empty and "date_tx" in df_noncommerce.columns:
            df_noncommerce = df_noncommerce[
                (df_noncommerce["date_tx"].dt.date >= tgl_range[0])
                & (df_noncommerce["date_tx"].dt.date <= tgl_range[1])
            ]
    else:
        df = df_sale.copy()
    return df, df_noncommerce


# ============================================================
# KPI Ringkasan
# ============================================================
def render_kpi(df, df_card, df_noncommerce, tgl_range):
    render_section_title("Ringkasan Performa", "💰")

    # Non-commerce
    if not df_noncommerce.empty:
        total_noncommerce = df_noncommerce["total_bayar"].sum()
        total_trx_noncommerce = df_noncommerce["bill_no"].nunique()
    else:
        total_noncommerce = 0
        total_trx_noncommerce = 0

    total_omzet = df["total_faktur"].sum()
    total_struk = df["faktur"].nunique()
    total_cash_klerk = _hitung_cash_klerk(df)
    total_omzet_reguler = total_omzet - total_noncommerce
    total_struk_reguler = total_struk - total_trx_noncommerce

    # Debit
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

    # Member
    if "cust_id" in df.columns:
        df["_is_member_kpi"] = df["cust_id"].apply(
            lambda x: str(x).strip() not in ["", "0", "0.0", "nan", "None"]
            and pd.notna(x)
        )
        total_sales_member = df[df["_is_member_kpi"]]["total_faktur"].sum()
        total_struk_member = df[df["_is_member_kpi"]]["faktur"].nunique()
    else:
        total_sales_member = 0
        total_struk_member = 0

    total_item = df["total_item"].sum() if "total_item" in df.columns else 0

    # Omzet
    st.markdown(
        '<div style="font-size:0.82rem;color:#8B949E;margin:0.75rem 0 0.5rem 0;">OMZET</div>',
        unsafe_allow_html=True,
    )
    metric_grid([
        {"label": "Omzet Reguler", "value": f"Rp {total_omzet_reguler:,.0f}", "variant": "accent"},
        {"label": "Omzet Non-Commerce", "value": f"Rp {total_noncommerce:,.0f}"},
        {"label": "Total Omzet", "value": f"Rp {total_omzet:,.0f}", "variant": "success"},
    ], cols=3)

    # Transaksi
    st.markdown(
        '<div style="font-size:0.82rem;color:#8B949E;margin:1rem 0 0.5rem 0;">TRANSAKSI</div>',
        unsafe_allow_html=True,
    )
    metric_grid([
        {"label": "Struk Reguler", "value": f"{int(total_struk_reguler):,}"},
        {"label": "Struk Non-Commerce", "value": f"{int(total_trx_noncommerce):,}"},
        {"label": "Total Item", "value": f"{int(total_item):,}"},
    ], cols=3)

    # Pembayaran
    st.markdown(
        '<div style="font-size:0.82rem;color:#8B949E;margin:1rem 0 0.5rem 0;">PEMBAYARAN</div>',
        unsafe_allow_html=True,
    )
    metric_grid([
        {"label": "Cash Klerk", "value": f"Rp {total_cash_klerk:,.0f}"},
        {"label": "Total Debit", "value": f"Rp {total_debit:,.0f}"},
        {"label": "Total E-Wallet", "value": f"Rp {total_ewallet:,.0f}"},
        {"label": "Sales Member", "value": f"Rp {total_sales_member:,.0f}",
         "sub": f"{total_struk_member} struk member", "variant": "warning"},
    ], cols=4)


# ============================================================
# Jam Ramai
# ============================================================
def render_jam_ramai(df):
    render_section_title("Jam Ramai Transaksi", "🕐")
    if "time_tx" not in df.columns or not df["time_tx"].notna().any():
        st.info("Kolom time_tx tidak ditemukan.")
        return

    df_time = df.copy()
    df_time["jam"] = df_time["time_tx"].apply(_get_hour)
    df_time = df_time.dropna(subset=["jam"])
    df_time["jam"] = df_time["jam"].astype(int)

    if df_time.empty:
        st.info("Tidak ada transaksi di rentang tanggal ini.")
        return

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
    st.bar_chart(chart_data, use_container_width=True, height=260)


# ============================================================
# Rekap Kasir
# ============================================================
def render_rekap_kasir(df, kasir_dict, noncommerce_per_kasir):
    render_section_title("Rekapitulasi per Kasir", "👤")
    if "user_id" not in df.columns:
        st.info("Kolom user_id tidak ditemukan.")
        return

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
        cash_klerk = _hitung_cash_klerk(grp)
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

    rekap_kasir = (
        pd.DataFrame(agg_rows)
        .sort_values("Sales Reguler", ascending=False)
        .reset_index(drop=True)
    )
    st.dataframe(rekap_kasir, use_container_width=True, hide_index=True)

    csv = rekap_kasir.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Rekap Kasir (CSV)",
        data=csv,
        file_name="rekap_kasir.csv",
        mime="text/csv",
    )


# ============================================================
# Lookup Nama Member dari tx_usi (2 jalur)
# ============================================================
def _build_member_lookup(df_usi):
    """
    Bangun lookup nama member dari tx_usi.
    Return 2 dict:
      - by_faktur: {faktur: {"nama": ..., "no_member": ...}}
      - by_no_member: {no_member: "nama"}
    """
    by_faktur = {}
    by_no_member = {}

    if df_usi.empty:
        return by_faktur, by_no_member

    required = ["faktur", "no_member", "member_name"]
    if not all(c in df_usi.columns for c in required):
        return by_faktur, by_no_member

    for _, row in df_usi.iterrows():
        faktur = str(row.get("faktur", "")).strip()
        no_member = str(row.get("no_member", "")).strip()
        nama = str(row.get("member_name", "")).strip()

        # Skip kalau nama kosong
        if not nama or nama == "nan":
            continue

        # Jalur 1: by faktur
        if faktur and faktur != "nan" and faktur not in by_faktur:
            by_faktur[faktur] = {"nama": nama, "no_member": no_member}

        # Jalur 2: by no_member
        if no_member and no_member != "nan" and no_member not in by_no_member:
            by_no_member[no_member] = nama

    return by_faktur, by_no_member


# ============================================================
# Detail Transaksi Member
# ============================================================
def render_detail_member(df, kasir_dict, df_usi, df_trans):
    """
    Section detail transaksi member.
    Nama member diambil dari tx_usi via 2 jalur:
      - Jalur A: faktur (tx_tsale.faktur → tx_usi.faktur)
      - Jalur B: no_member (tx_tsale.cust_id → tx_usi.no_member)
      - Jalur C: tx_trans.member → tx_usi.no_member (untuk cross-check)
    """
    render_section_title("Detail Transaksi Member", "👥")

    if "cust_id" not in df.columns:
        st.warning("Kolom `cust_id` tidak ditemukan di tx_tsale.")
        return

    # Flag member di tx_tsale
    df = df.copy()
    df["is_member"] = df["cust_id"].apply(
        lambda x: str(x).strip() not in ["", "0", "0.0", "nan", "None"]
        and pd.notna(x)
    )
    df_member = df[df["is_member"] == True].copy()

    if df_member.empty:
        st.info("Tidak ada transaksi member di rentang tanggal ini.")
        return

    # ---- Build 2 lookup dari tx_usi ----
    lookup_faktur, lookup_no_member = _build_member_lookup(df_usi)

    # ---- Bangun view dari tx_tsale ----
    df_member_view = df_member[[
        "faktur", "date_tx", "time_tx", "user_id", "cust_id",
        "total_faktur", "total_item"
    ]].copy()

    df_member_view["Nama Kasir"] = (
        df_member_view["user_id"].astype(str).map(kasir_dict).fillna("-")
    )

    # ---- JALUR A: match by faktur ----
    def get_nama_by_faktur(faktur_val):
        return lookup_faktur.get(str(faktur_val).strip(), {}).get("nama", "")

    # ---- JALUR B: match by cust_id (no_member) ----
    def get_nama_by_cust(cust_val):
        return lookup_no_member.get(str(cust_val).strip(), "")

    # Gabungkan: prioritas faktur dulu, fallback ke cust_id
    df_member_view["Nama Member"] = df_member_view.apply(
        lambda r: (
            get_nama_by_faktur(r["faktur"])          # Jalur A
            or get_nama_by_cust(r["cust_id"])        # Jalur B (fallback)
            or "-"
        ),
        axis=1,
    )

    # ---- JALUR C: cross-check dengan tx_trans ----
    # Kalau nama masih "-", coba cari dari tx_trans.member
    if not df_trans.empty and "member" in df_trans.columns and "bill_no" in df_trans.columns:
        # Map bill_no -> member (dari tx_trans)
        bill_to_member = (
            df_trans[df_trans["member"].notna() & (df_trans["member"].astype(str) != "")]
            .groupby("bill_no")["member"]
            .first()
            .to_dict()
        )
        # Map bill_no (dari faktur) ke nama via lookup_no_member
        def get_nama_from_trans(faktur_val):
            try:
                bill_no = str(faktur_val).split("-")[-1]
                bill_key = str(int(bill_no)) if bill_no.isdigit() else bill_no
            except Exception:
                return ""
            member_id = bill_to_member.get(bill_key, "")
            if not member_id:
                return ""
            return lookup_no_member.get(str(member_id).strip(), "")

        # Isi yang masih "-" dengan jalur C
        mask_kosong = df_member_view["Nama Member"] == "-"
        if mask_kosong.any():
            df_member_view.loc[mask_kosong, "Nama Member"] = (
                df_member_view.loc[mask_kosong, "faktur"]
                .apply(get_nama_from_trans)
            )
            # Kalau masih kosong, ganti ke "-"
            df_member_view["Nama Member"] = df_member_view["Nama Member"].replace("", "-")

    # ---- No. Member ----
    df_member_view["No. Member"] = df_member_view["cust_id"].astype(str)

    # ---- Rename kolom ----
    df_member_view = df_member_view.rename(columns={
        "faktur": "Faktur",
        "date_tx": "Tanggal",
        "time_tx": "Jam",
        "user_id": "NIK Kasir",
        "total_faktur": "Total",
        "total_item": "Item",
    })

    df_member_view = df_member_view[[
        "Faktur", "Tanggal", "Jam", "Nama Kasir",
        "Nama Member", "No. Member", "Item", "Total"
    ]].sort_values(["Tanggal", "Jam"], ascending=[False, False]).reset_index(drop=True)

    # ---- Debug expander ----
    with st.expander("🔍 Debug Lookup Member", expanded=False):
        st.write(f"Total member di tx_usi: **{len(lookup_faktur)}** (by faktur), "
                 f"**{len(lookup_no_member)}** (by no_member)")
        st.write(f"Total struk member di tx_tsale: **{len(df_member_view)}**")

        # Hitung berapa yang dapat nama
        dapat_nama = (df_member_view["Nama Member"] != "-").sum()
        st.write(f"✅ Berhasil dapat nama: **{dapat_nama}** / {len(df_member_view)}")

        # Preview contoh key
        if lookup_faktur:
            st.write("Contoh key by faktur:", list(lookup_faktur.keys())[:5])
        if lookup_no_member:
            st.write("Contoh key by no_member:", list(lookup_no_member.keys())[:5])
        st.write("Contoh cust_id di transaksi:",
                 df_member_view["No. Member"].unique()[:5].tolist())

    # ---- Ringkasan ----
    total_struk = len(df_member_view)
    total_member_unik = df_member_view["No. Member"].nunique()
    total_sales = df_member_view["Total"].sum()
    avg_basket = total_sales / total_struk if total_struk > 0 else 0
    avg_kunjungan = total_struk / total_member_unik if total_member_unik > 0 else 0

    metric_grid([
        {"label": "Jumlah Struk Member", "value": f"{total_struk:,}", "variant": "accent"},
        {"label": "Member Unik", "value": f"{total_member_unik:,}"},
        {"label": "Total Sales Member", "value": f"Rp {total_sales:,.0f}", "variant": "success"},
        {"label": "Rata-rata Basket", "value": f"Rp {avg_basket:,.0f}", "variant": "warning"},
    ], cols=4)

    metric_grid([
        {"label": "Avg Kunjungan / Member", "value": f"{avg_kunjungan:.2f}x",
         "sub": "rata-rata frekuensi belanja per member"},
        {"label": "Member dengan >1x Belanja",
         "value": f"{(df_member_view.groupby('No. Member').size() > 1).sum():,}"},
        {"label": "Coverage Nama",
         "value": f"{(df_member_view['Nama Member'] != '-').sum()} / {total_struk}",
         "sub": "struk dengan nama terisi"},
    ], cols=3)

    # ---- Ranking Member ----
    render_section_title("Ranking Member Terbanyak", "🏆")

    ranking = (
        df_member_view.groupby(["No. Member", "Nama Member"])
        .agg(
            Jumlah_Struk=("Faktur", "count"),
            Total_Belanja=("Total", "sum"),
            Total_Item=("Item", "sum"),
            Kunjungan_Pertama=("Jam", "min"),
            Kunjungan_Terakhir=("Jam", "max"),
        )
        .reset_index()
        .sort_values(["Jumlah_Struk", "Total_Belanja"], ascending=[False, False])
        .reset_index(drop=True)
    )
    ranking.index = ranking.index + 1
    ranking = ranking.rename(columns={
        "Jumlah_Struk": "Struk",
        "Total_Belanja": "Total Belanja",
        "Total_Item": "Item",
        "Kunjungan_Pertama": "Jam Pertama",
        "Kunjungan_Terakhir": "Jam Terakhir",
    })

    top_n = st.slider("Tampilkan Top N member:", 5, 50, 10, key="member_topn")
    ranking_show = ranking.head(top_n).copy()
    ranking_show["Avg Basket"] = ranking_show["Total Belanja"] / ranking_show["Struk"]

    st.dataframe(
        ranking_show[[
            "No. Member", "Nama Member", "Struk",
            "Item", "Total Belanja", "Avg Basket",
            "Jam Pertama", "Jam Terakhir",
        ]],
        use_container_width=True,
    )

    csv_rank = ranking.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Ranking Member (CSV)",
        data=csv_rank,
        file_name="ranking_member.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # ---- Detail Transaksi ----
    render_section_title("Detail Transaksi", "📋")

    col_f1, col_f2 = st.columns([2, 2])
    with col_f1:
        search = st.text_input(
            "🔎 Cari Faktur / No. Member / Nama",
            placeholder="Contoh: 409-04109W38 atau RAIHAN",
            key="member_search",
        )
    with col_f2:
        list_kasir = ["Semua"] + sorted(df_member_view["Nama Kasir"].unique().tolist())
        filter_kasir = st.selectbox("Filter Kasir", list_kasir, key="member_filter_kasir")

    df_show = df_member_view.copy()
    if search:
        kw = str(search).strip().lower()
        mask = (
            df_show["Faktur"].astype(str).str.lower().str.contains(kw, na=False)
            | df_show["No. Member"].astype(str).str.lower().str.contains(kw, na=False)
            | df_show["Nama Member"].astype(str).str.lower().str.contains(kw, na=False)
        )
        df_show = df_show[mask]

    if filter_kasir != "Semua":
        df_show = df_show[df_show["Nama Kasir"] == filter_kasir]

    st.caption(f"Menampilkan {len(df_show)} dari {len(df_member_view)} struk member.")
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    csv = df_show.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Detail Member (CSV)",
        data=csv,
        file_name="detail_member.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================
# MAIN RENDER
# ============================================================
def render_dashboard():
    render_header(
        "Dashboard",
        "Ringkasan performa toko & rekap kasir",
        icon="📊",
    )

    if not render_upload_section():
        st.stop()

    df_sale, df_card, df_receipt, df_noncommerce, df_usi, kasir_dict = load_and_prepare()
    tgl_range = render_date_filter(df_sale)
    df, df_noncommerce = apply_filter(df_sale, df_noncommerce, tgl_range)
    st.caption(f"Menampilkan {len(df)} transaksi.")

    # Non-commerce per kasir
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

    render_kpi(df, df_card, df_noncommerce, tgl_range)
    render_jam_ramai(df)
    render_rekap_kasir(df, kasir_dict, noncommerce_per_kasir)
    render_detail_member(df, kasir_dict, df_usi)

    # Navigasi
    render_section_title("Halaman Analisis", "📂")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        if st.button("📊 1 PSM per PLU", use_container_width=True, key="dash_nav_psm"):
            st.switch_page("pages/1_PSM_per_PLU.py")
        if st.button("📦 3 Topup Flaz", use_container_width=True, key="dash_nav_topup"):
            st.switch_page("pages/5_Topup_Flaz.py")
    with col_a2:
        if st.button("🎁 2 SG per Paket", use_container_width=True, key="dash_nav_sg"):
            st.switch_page("pages/2_SG_per_Paket.py")
        if st.button("🧾 4 Suger", use_container_width=True, key="dash_nav_suger"):
            st.switch_page("pages/3_struk_Suger.py")

    render_section_title("Tools", "🔧")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🔍 Cek Struk Detail", use_container_width=True, key="dash_nav_cek_struk"):
            st.switch_page("pages/7_Cek_Struk_Detail.py")
    with col_t2:
        if st.button("❌ Void Transaksi", use_container_width=True, key="dash_nav_void"):
            st.switch_page("pages/6_Cek_Struk_Void.py")