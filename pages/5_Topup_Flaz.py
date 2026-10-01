import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
from utils.common import load_tables
from utils.nav_helper import render_back_to_dashboard, safe_stop
from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style

setup_anonim_page("Topup Flaz", "📦")
apply_nav_style()

st.title("📱 Laporan Topup Flaz")
st.markdown("Menampilkan semua transaksi topup Flaz dari tabel `tx_trans_non_commerce`.")

db_file = st.session_state.get("db_path", None)

if not db_file:
    st.warning("Belum ada database. Buka halaman Home dulu untuk upload ZIP.")
    st.save("topup")

st.success("Database: " + st.session_state.get("db_name", ""))

try:
    dfs = load_tables(db_file, ["tx_trans_non_commerce"])
    df_topup = dfs.get("tx_trans_non_commerce", pd.DataFrame())

    if df_topup.empty:
        st.warning("Tidak ada data di tabel tx_trans_non_commerce.")
        st.save("topup")

    # Konversi tipe
    df_topup["date_tx"] = pd.to_datetime(df_topup["date_tx"], errors="coerce")

    for c in ["price", "qty", "disc", "saving"]:
        if c in df_topup.columns:
            df_topup[c] = pd.to_numeric(df_topup[c], errors="coerce").fillna(0)

    if "bill_no" in df_topup.columns:
        df_topup["bill_no"] = pd.to_numeric(df_topup["bill_no"], errors="coerce")

    # ============================================================
    # FILTER: hanya baris yang ada nominalnya (topup Flaz, bukan admin)
    # ============================================================
    df_topup = df_topup[df_topup["price"] > 0].copy()

    # Total bayar per baris
    df_topup["total_bayar"] = (df_topup["price"] * df_topup["qty"]) - df_topup["disc"]

    # ============================================================
    # FILTER TANGGAL
    # ============================================================
    st.subheader("📅 Filter Tanggal")

    tgl_range = ()
    if df_topup["date_tx"].notna().any():
        min_d = df_topup["date_tx"].min().date()
        max_d = df_topup["date_tx"].max().date()
        tgl_range = st.date_input(
            "Rentang Tanggal",
            value=(min_d, max_d),
            min_value=min_d,
            max_value=max_d,
            key="topup_tgl",
        )
        if len(tgl_range) == 2:
            mask = (
                df_topup["date_tx"].dt.date >= tgl_range[0]
            ) & (df_topup["date_tx"].dt.date <= tgl_range[1])
            df = df_topup[mask].copy()
        else:
            df = df_topup.copy()
    else:
        df = df_topup.copy()

    if df.empty:
        st.warning("Tidak ada transaksi di rentang tanggal ini.")
        st.save("topup")

    # ============================================================
    # KPI
    # ============================================================
    st.markdown("---")
    st.subheader("💰 Ringkasan Topup Flaz")

    total_transaksi = len(df)  # 1 baris = 1 transaksi
    total_nominal = df["total_bayar"].sum()

    c1, c2 = st.columns(2)
    c1.metric("🔢 Jumlah Topup", format(int(total_transaksi), ","))
    c2.metric("💵 Total Nominal", "Rp " + format(total_nominal, ",.0f"))

    # ============================================================
    # GRAFIK JAM TRANSAKSI
    # ============================================================
    st.markdown("---")
    st.subheader("🕐 Jam Transaksi Topup Flaz")

    if "trans_time" in df.columns and df["trans_time"].notna().any():
        df_time = df.copy()

        def get_hour(t):
            try:
                s = str(t).strip()
                if ":" in s:
                    return int(s.split(":")[0])
                return None
            except Exception:
                return None

        df_time["jam"] = df_time["trans_time"].apply(get_hour)
        df_time = df_time.dropna(subset=["jam"])
        df_time["jam"] = df_time["jam"].astype(int)

        if not df_time.empty:
            per_jam = (
                df_time.groupby("jam")
                .size()
                .reset_index()
                .rename(columns={0: "Jumlah"})
            )

            all_hours = pd.DataFrame({"jam": range(24)})
            per_jam = all_hours.merge(per_jam, on="jam", how="left").fillna(0)
            per_jam["Jumlah"] = per_jam["Jumlah"].astype(int)

            st.bar_chart(per_jam.set_index("jam")["Jumlah"])

            per_jam_aktif = per_jam[per_jam["Jumlah"] > 0]
            if not per_jam_aktif.empty:
                jam_teramai = per_jam_aktif.loc[per_jam_aktif["Jumlah"].idxmax()]
                jam_tersepi = per_jam_aktif.loc[per_jam_aktif["Jumlah"].idxmin()]

                col_a, col_b = st.columns(2)
                with col_a:
                    st.success(
                        "🔥 Jam Teramai: "
                        + str(int(jam_teramai["jam"])).zfill(2) + ":00"
                        + " — "
                        + str(int(jam_teramai["Jumlah"]))
                        + " transaksi"
                    )
                with col_b:
                    st.warning(
                        "❄️ Jam Tersepi: "
                        + str(int(jam_tersepi["jam"])).zfill(2) + ":00"
                        + " — "
                        + str(int(jam_tersepi["Jumlah"]))
                        + " transaksi"
                    )
        else:
            st.info("Kolom trans_time tidak berisi data valid.")
    else:
        st.info("Kolom trans_time tidak ditemukan.")

    # ============================================================
    # DETAIL TRANSAKSI
    # ============================================================
    st.markdown("---")
    st.subheader("📋 Detail Transaksi")

    cols_show = [c for c in [
        "date_tx", "trans_time", "bill_no", "user_id",
        "plu", "price", "qty", "total_bayar",
        "info_tx",
    ] if c in df.columns]

    df_detail = df[cols_show].sort_values(
        ["date_tx", "trans_time"], ascending=[False, False]
    ).reset_index(drop=True)

    # Rename kolom biar lebih jelas
    df_detail = df_detail.rename(columns={
        "date_tx": "Tanggal",
        "trans_time": "Jam",
        "bill_no": "Bill No",
        "user_id": "NIK Kasir",
        "plu": "PLU",
        "price": "Harga",
        "qty": "Qty",
        "total_bayar": "Total Bayar",
        "info_tx": "No Kartu Flaz",
    })

    st.dataframe(df_detail, use_container_width=True)

    # ============================================================
    # DOWNLOAD CSV
    # ============================================================
    csv = df_detail.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Detail Topup Flaz (CSV)",
        data=csv,
        file_name="topup_flaz.csv",
        mime="text/csv",
    )

    # ============================================================
    # DEBUG
    # ============================================================
    with st.expander("🔍 Debug"):
        st.write("Total baris (setelah filter price > 0): " + str(len(df_topup)))
        st.write("Setelah filter tanggal: " + str(len(df)))
        st.write("Kolom: ", df_topup.columns.tolist())

except Exception as e:
    st.error("Error: " + str(e))
    st.exception(e)

render_nav_universal("topup")
render_back_to_dashboard("topup")