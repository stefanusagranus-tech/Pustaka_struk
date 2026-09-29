import streamlit as st
import pandas as pd
import os
import shutil
from utils.common import (
    extract_zip_and_find_db,
    load_tables,
    build_kasir_dict,
)

st.set_page_config(
    page_title="Dashboard POS",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Dashboard POS")
st.markdown("Upload database, lalu lihat ringkasan performa toko di bawah.")

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
        "tx_tsale",
        "tx_tsale_card",
        "tx_trans",
        "log_connection",
    ]
    dfs = load_tables(db_path, tables)
    return dfs


try:
    dfs = get_data(st.session_state["db_path"])
    df_sale = dfs.get("tx_tsale", pd.DataFrame())
    df_card = dfs.get("tx_tsale_card", pd.DataFrame())
    df_connection = dfs.get("log_connection", pd.DataFrame())
    
    # Bangun dictionary NIK -> Nama
    kasir_dict = build_kasir_dict(df_connection)
except Exception as e:
    st.error("Gagal load database: " + str(e))
    st.stop()

if df_sale.empty:
    st.error("Tabel tx_tsale kosong atau tidak ditemukan.")
    st.stop()

# ============================================================
# PREPARE DATA
# ============================================================
df_sale["date_tx"] = pd.to_datetime(df_sale["date_tx"], errors="coerce")

# Konversi numerik
num_cols = ["total_faktur", "cash", "card", "discount", "promo_disc",
            "charity", "cash_out", "wallet", "ol_payment", "voucher",
            "total_item"]
for c in num_cols:
    if c in df_sale.columns:
        df_sale[c] = pd.to_numeric(df_sale[c], errors="coerce").fillna(0)

# Member: pakai cust_id (bukan member)
if "cust_id" in df_sale.columns:
    df_sale["cust_id_str"] = df_sale["cust_id"].astype(str).str.strip()

# Member: pakai cust_id (bukan member)
if "cust_id" in df_sale.columns:
    df_sale["cust_id_str"] = df_sale["cust_id"].astype(str).str.strip()

# ============================================================
# FILTER TANGGAL
# ============================================================
st.subheader("📅 Filter Tanggal")

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
        mask = (
            df_sale["date_tx"].dt.date >= tgl_range[0]
        ) & (df_sale["date_tx"].dt.date <= tgl_range[1])
        df = df_sale[mask].copy()
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
        safe_sum("total_faktur")
        + safe_sum("charity")
        - safe_sum("discount")
        - safe_sum("card")
        - safe_sum("cash_out")
        - safe_sum("wallet")
        - safe_sum("ol_payment")
        - safe_sum("voucher")
    )


# ============================================================
# KPI UTAMA
# ============================================================
st.markdown("---")
st.subheader("💰 Ringkasan Performa")

total_omzet = df["total_faktur"].sum()
total_struk = df["faktur"].nunique()
total_cash_klerk = hitung_cash_klerk(df)

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

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Total Omzet", "Rp " + format(total_omzet, ",.0f"))
c2.metric("🧾 Total Struk", format(total_struk, ","))
c3.metric("💵 Cash Klerk", "Rp " + format(total_cash_klerk, ",.0f"))
c4.metric("💳 Total Debit", "Rp " + format(total_debit, ",.0f"))

c5, c6, c7, c8 = st.columns(4)
c5.metric("📱 Total E-Wallet", "Rp " + format(total_ewallet, ",.0f"))
c6.metric("👥 Sales Member", "Rp " + format(total_sales_member, ",.0f"))

total_item = df["total_item"].sum() if "total_item" in df.columns else 0
rata_struk = total_omzet / total_struk if total_struk > 0 else 0

c7.metric("📦 Total Item", format(int(total_item), ","))
c8.metric("📊 Rata-rata/Struk", "Rp " + format(rata_struk, ",.0f"))

# ============================================================
# GRAFIK JAM RAMAI
# ============================================================
st.markdown("---")
st.subheader("🕐 Jam Ramai Transaksi")

if "time_tx" in df.columns and df["time_tx"].notna().any():
    # Konversi time_tx ke jam (0-23)
    df_time = df.copy()

    def get_hour(t):
        try:
            s = str(t).strip()
            # Format "HH:MM:SS" atau "HH:MM"
            if ":" in s:
                return int(s.split(":")[0])
            return None
        except Exception:
            return None

    df_time["jam"] = df_time["time_tx"].apply(get_hour)
    df_time = df_time.dropna(subset=["jam"])
    df_time["jam"] = df_time["jam"].astype(int)

    if not df_time.empty:
        # Hitung jumlah transaksi per jam
        per_jam = (
            df_time.groupby("jam")["faktur"]
            .nunique()
            .reset_index()
            .rename(columns={"faktur": "Jumlah_Transaksi"})
        )

        # Lengkapi semua jam 0-23
        all_hours = pd.DataFrame({"jam": range(24)})
        per_jam = all_hours.merge(per_jam, on="jam", how="left").fillna(0)
        per_jam["Jumlah_Transaksi"] = per_jam["Jumlah_Transaksi"].astype(int)

        # Bar chart
        chart_data = per_jam.set_index("jam")["Jumlah_Transaksi"]
        st.bar_chart(chart_data, use_container_width=True)

        # Cari jam teramai & tersepi (hanya dari jam yang ada transaksi)
        per_jam_aktif = per_jam[per_jam["Jumlah_Transaksi"] > 0]

        if not per_jam_aktif.empty:
            jam_teramai = per_jam_aktif.loc[
                per_jam_aktif["Jumlah_Transaksi"].idxmax()
            ]
            jam_tersepi = per_jam_aktif.loc[
                per_jam_aktif["Jumlah_Transaksi"].idxmin()
            ]

            col_a, col_b = st.columns(2)
            with col_a:
                st.success(
                    "🔥 **Jam Teramai:** "
                    + str(int(jam_teramai["jam"])).zfill(2) + ":00"
                    + " — "
                    + str(int(jam_teramai["Jumlah_Transaksi"]))
                    + " transaksi"
                )
            with col_b:
                st.warning(
                    "❄️ **Jam Tersepi:** "
                    + str(int(jam_tersepi["jam"])).zfill(2) + ":00"
                    + " — "
                    + str(int(jam_tersepi["Jumlah_Transaksi"]))
                    + " transaksi"
                )

            # Tabel distribusi per jam
            with st.expander("📋 Lihat Distribusi per Jam"):
                per_jam_display = per_jam.copy()
                per_jam_display["Jam"] = per_jam_display["jam"].apply(
                    lambda x: str(x).zfill(2) + ":00"
                )
                per_jam_display = per_jam_display[["Jam", "Jumlah_Transaksi"]]
                st.dataframe(per_jam_display, use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ada transaksi di rentang tanggal ini.")
    else:
        st.info("Kolom time_tx tidak berisi data valid.")
else:
    st.info("Kolom time_tx tidak ditemukan di tx_tsale.")


# ============================================================
# BREAKDOWN DEBIT PER BANK
# ============================================================
st.markdown("---")
st.subheader("💳 Sales Debit per Bank")

if not df_card.empty and "bank" in df_card.columns and "amount" in df_card.columns:
    df_card_temp = df_card.copy()
    df_card_temp["amount"] = pd.to_numeric(
        df_card_temp["amount"], errors="coerce"
    ).fillna(0)

    # Filter tanggal
    if "date_tx" in df_card_temp.columns:
        df_card_temp["date_tx"] = pd.to_datetime(
            df_card_temp["date_tx"], errors="coerce"
        )
        if len(tgl_range) == 2:
            df_card_temp = df_card_temp[
                (df_card_temp["date_tx"].dt.date >= tgl_range[0])
                & (df_card_temp["date_tx"].dt.date <= tgl_range[1])
            ]

    # Mapping kode bank ke nama
    BANK_MAP = {
        1: "BCA",
        2: "Mandiri",
        3: "BNI",
        4: "BRI",
        5: "CIMB Niaga",
        6: "Danamon",
        7: "Permata",
        8: "Maybank",
        9: "BCA (2)",
        10: "Mandiri (2)",
        11: "BNI (2)",
        12: "BRI (2)",
        13: "BCA (3)",
        14: "Mandiri (3)",
        15: "BNI (3)",
        16: "BRI (3)",
        17: "Lainnya",
    }

    def get_bank_name(bank_code):
        try:
            code = int(float(bank_code))
            return BANK_MAP.get(code, "Bank #" + str(code))
        except Exception:
            return "Tidak diketahui"

    df_card_temp["Nama_Bank"] = df_card_temp["bank"].apply(get_bank_name)

    # Group by nama bank
    rekap_bank = (
        df_card_temp.groupby("Nama_Bank")
        .agg(
            Jumlah_Transaksi=("faktur", "nunique"),
            Total_Nominal=("amount", "sum"),
        )
        .reset_index()
        .sort_values("Total_Nominal", ascending=False)
    )

    if not rekap_bank.empty:
        # Bar chart
        chart_bank = rekap_bank.set_index("Nama_Bank")["Total_Nominal"]
        st.bar_chart(chart_bank, use_container_width=True)

        # Tabel
        rekap_bank_display = rekap_bank.copy()
        rekap_bank_display["Total_Nominal"] = rekap_bank_display["Total_Nominal"].apply(
            lambda x: "Rp " + format(x, ",.0f")
        )
        st.dataframe(rekap_bank_display, use_container_width=True, hide_index=True)

        # Total debit
        total_debit_bank = df_card_temp["amount"].sum()
        st.info(
            "Total Debit: **Rp " + format(total_debit_bank, ",.0f")
            + "** dari **" + str(df_card_temp["faktur"].nunique())
            + "** transaksi"
        )
    else:
        st.info("Tidak ada transaksi debit di rentang tanggal ini.")
else:
    st.info("Tabel tx_tsale_card tidak ditemukan atau kosong.")


# ============================================================
# TABEL PER KASIR
# ============================================================
st.markdown("---")
st.subheader("👤 Rekapitulasi per Kasir")

if "user_id" in df.columns:
    # Siapkan kolom is_member dari cust_id
    if "cust_id" in df.columns:
        df["is_member"] = df["cust_id"].apply(
            lambda x: str(x).strip() not in ["", "0", "0.0", "nan", "None"]
                      and pd.notna(x)
        )
    else:
        df["is_member"] = False

    # Agregasi
    agg_rows = []
    for kasir, grp in df.groupby("user_id"):
        # Sales Personil
        sales_personil = grp["total_faktur"].sum()

        # STD Personil
        std_personil = grp["faktur"].nunique()

        # Sales Member
        grp_member = grp[grp["is_member"] == True]
        sales_member = grp_member["total_faktur"].sum() if not grp_member.empty else 0
        std_member = grp_member["faktur"].nunique() if not grp_member.empty else 0

        # Cash Klerk
        cash_klerk = hitung_cash_klerk(grp)

        # Debit (dari df_card, filter per kasir)
        total_debit_kasir = 0
        if not df_card.empty and "user_id" in df_card.columns:
            df_card_k = df_card.copy()
            df_card_k["amount"] = pd.to_numeric(
                df_card_k["amount"], errors="coerce"
            ).fillna(0)
            if "date_tx" in df_card_k.columns:
                df_card_k["date_tx"] = pd.to_datetime(
                    df_card_k["date_tx"], errors="coerce"
                )
                if len(tgl_range) == 2:
                    df_card_k = df_card_k[
                        (df_card_k["date_tx"].dt.date >= tgl_range[0])
                        & (df_card_k["date_tx"].dt.date <= tgl_range[1])
                    ]
            df_card_k = df_card_k[df_card_k["user_id"].astype(str) == str(kasir)]
            total_debit_kasir = df_card_k["amount"].sum()

        # E-Wallet
        ewallet_kasir = grp["wallet"].sum() if "wallet" in grp.columns else 0

        nik = str(kasir)
        nama_kasir = kasir_dict.get(nik, "-")
        
        agg_rows.append({
            "NIK": nik,
            "Nama_Kasir": nama_kasir,
            "Sales_Personil": sales_personil,
            "STD_Personil": int(std_personil),
            "Sales_Member": sales_member,
            "STD_Member": int(std_member),
            "Cash_Klerk": cash_klerk,
            "Debit": total_debit_kasir,
            "E_Wallet": ewallet_kasir,
        })

    rekap_kasir = pd.DataFrame(agg_rows).sort_values(
        "Sales_Personil", ascending=False
    ).reset_index(drop=True)

    # Tampilkan dalam format tabel yang rapi
    rekap_display = rekap_kasir.copy()
    rekap_display["Sales_Personil"] = rekap_display["Sales_Personil"].apply(
        lambda x: "Rp " + format(x, ",.0f")
    )
    rekap_display["Sales_Member"] = rekap_display["Sales_Member"].apply(
        lambda x: "Rp " + format(x, ",.0f")
    )
    rekap_display["Cash_Klerk"] = rekap_display["Cash_Klerk"].apply(
        lambda x: "Rp " + format(x, ",.0f")
    )
    rekap_display["Debit"] = rekap_display["Debit"].apply(
        lambda x: "Rp " + format(x, ",.0f")
    )
    rekap_display["E_Wallet"] = rekap_display["E_Wallet"].apply(
        lambda x: "Rp " + format(x, ",.0f")
    )
    
    st.caption("Terdeteksi " + str(len(kasir_dict)) + " kasir dari log_connection.")
    rekap_display = rekap_display.rename(columns={
        "NIK": "NIK",
        "Nama_Kasir": "Nama Kasir",
        "Sales_Personil": "Sales Personil",
        "STD_Personil": "STD Personil",
        "Sales_Member": "Sales Member",
        "STD_Member": "STD Member",
        "Cash_Klerk": "Cash Klerk",
        "E_Wallet": "E-Wallet",
    })

    st.dataframe(rekap_display, use_container_width=True, hide_index=True)

    # Total baris
    st.markdown("**Total:**")
    total_row = pd.DataFrame([{
        "NIK": "TOTAL",
        "Nama Kasir": "-",
        "Sales Personil": "Rp " + format(rekap_kasir["Sales_Personil"].sum(), ",.0f"),
        "STD Personil": int(rekap_kasir["STD_Personil"].sum()),
        "Sales Member": "Rp " + format(rekap_kasir["Sales_Member"].sum(), ",.0f"),
        "STD Member": int(rekap_kasir["STD_Member"].sum()),
        "Cash Klerk": "Rp " + format(rekap_kasir["Cash_Klerk"].sum(), ",.0f"),
        "Debit": "Rp " + format(rekap_kasir["Debit"].sum(), ",.0f"),
        "E-Wallet": "Rp " + format(rekap_kasir["E_Wallet"].sum(), ",.0f"),
    }])
    st.dataframe(total_row, use_container_width=True, hide_index=True)

    # Download CSV
    csv = rekap_kasir.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Rekap Kasir (CSV)",
        data=csv,
        file_name="rekap_kasir.csv",
        mime="text/csv",
    )
else:
    st.info("Kolom user_id tidak ditemukan.")


# ============================================================
# HALAMAN LAIN
# ============================================================
st.markdown("---")
st.markdown("### 📌 Halaman Lain")
st.markdown(
    "Buka **sidebar kiri** untuk: "
    "- **1 PSM per PLU** — Laporan PSM berdasarkan PLU\n"
    "- **2 SG per Paket** — Laporan Serba Gratis per paket"
)


# ============================================================
# DEBUG
# ============================================================
with st.expander("🔍 Debug"):
    st.write("Total baris tx_tsale: " + str(len(df_sale)))
    st.write("Total baris tx_tsale_card: " + str(len(df_card)))
    st.write("Rentang tanggal: " + str(tgl_range))
    st.write("Kolom tx_tsale: ", df_sale.columns.tolist())
    st.write("Kolom tx_tsale_card: ", df_card.columns.tolist() if not df_card.empty else "kosong")