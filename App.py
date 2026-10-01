"""
App.py — Pustaka Struk Main App
Include: Login + Menu + Dashboard + Idea Box.
"""
import streamlit as st
import pandas as pd
import os
import shutil
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Tambah path root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.common import (
    extract_zip_and_find_db,
    load_tables,
    build_kasir_dict_from_receipt,
)
from utils.anonim import setup_anonim_page, apply_nav_style
from utils.auth import (
    init_auth_state,
    render_login_screen,
    render_menu_screen,
    logout,
    back_to_menu,
)

# ============================================================
# SETUP HALAMAN
# ============================================================
setup_anonim_page("Pustaka Struk", "📦")
apply_nav_style()

# ============================================================
# INIT AUTH
# ============================================================
init_auth_state()

# ============================================================
# PATH FILE IDEA BOX
# ============================================================
IDEAS_FILE = "docs/ideas.json"
ARCHIVE_FILE = "docs/ideas_archive.json"

# ============================================================
# HELPER JSON
# ============================================================
def load_json(filepath, default):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(filepath, data):
    data["last_update"] = datetime.now().isoformat()
    if "ideas" in data:
        data["total_ideas"] = len(data["ideas"])
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_ideas():
    return load_json(IDEAS_FILE, {
        "last_update": datetime.now().isoformat(),
        "total_ideas": 0,
        "ideas": [],
    })


def load_archive():
    return load_json(ARCHIVE_FILE, {
        "last_update": datetime.now().isoformat(),
        "total_ideas": 0,
        "ideas": [],
    })


def save_ideas(data):
    save_json(IDEAS_FILE, data)


def save_archive(data):
    save_json(ARCHIVE_FILE, data)


# ============================================================
# HAPUS / RESTORE IDE
# ============================================================
def hapus_ide(index, soft=True):
    ideas_data = load_ideas()
    archive_data = load_archive()
    if index < 0 or index >= len(ideas_data["ideas"]):
        return False
    idea = ideas_data["ideas"].pop(index)
    if soft:
        idea["tanggal_dihapus"] = datetime.now().isoformat()
        idea["alasan"] = "dihapus_user"
        archive_data["ideas"].append(idea)
        save_archive(archive_data)
    save_ideas(ideas_data)
    return True


def restore_ide(archive_index):
    ideas_data = load_ideas()
    archive_data = load_archive()
    if archive_index < 0 or archive_index >= len(archive_data["ideas"]):
        return False
    idea = archive_data["ideas"].pop(archive_index)
    idea.pop("tanggal_dihapus", None)
    idea.pop("alasan", None)
    idea["status"] = "pending"
    ideas_data["ideas"].append(idea)
    save_ideas(ideas_data)
    save_archive(archive_data)
    return True


def hapus_permanen(archive_index):
    archive_data = load_archive()
    if archive_index < 0 or archive_index >= len(archive_data["ideas"]):
        return False
    archive_data["ideas"].pop(archive_index)
    save_archive(archive_data)
    return True


# ============================================================
# GENERATE BLUEPRINT DARI IDE
# ============================================================
def generate_steps(idea):
    return [
        f"Analisis kebutuhan: {idea['judul']}",
        "Baca tabel terkait di SQLite",
        f"Bikin query pandas untuk {idea['deskripsi'][:50]}...",
        f"Bikin file: {', '.join(idea['file_target'])}",
        "Bikin visualisasi (chart/table)",
        "Tambah filter interaktif (date, kasir, dll)",
        "Tambah tombol download CSV",
        "Uji dengan data 27/09/2026",
        "Commit + push ke GitHub",
        "Update progress.json",
    ]


def generate_blueprint_md(idea):
    steps = generate_steps(idea)
    md = f"""# BLUEPRINT: {idea['judul']}

**ID:** {idea['id']}
**Kategori:** {idea['kategori']}
**Prioritas:** {idea['prioritas']}
**Estimasi:** {idea['estimasi_hari']} hari
**Tanggal Dibuat:** {idea['tanggal_dibuat']}

---

## Deskripsi

{idea['deskripsi']}

---

## Tujuan

Bikin fitur/halaman baru di proyek Pustaka Struk
untuk **{idea['judul'].lower()}**.

---

## File Target

{chr(10).join(f'- `{f}`' for f in idea['file_target'])}

---

## Step-by-Step

"""
    for i, step in enumerate(steps, 1):
        md += f"{i}. [ ] {step}\n"

    md += f"""

---

## Sumber Data

Tabel SQLite yang mungkin dipakai:
- `tx_tsale` (header penjualan)
- `tx_trans` (detail item)
- `log_receipt_prn` (data struk)
- `log_cashier` (data kasir)

---

## Catatan

{idea.get('catatan', '-')}

---

## Instruksi Untuk AI
## Instruksi Untuk AI

```

Halo AI, aku punya proyek Pustaka Struk (Dashboard internal pakai Streamlit + SQLite).
Aku mau nambah fitur baru dengan spesifikasi di atas.

Tolong:

1. Baca blueprint ini sampai habis.
2. Konfirmasi kalau sudah paham.
3. Bikin kodenya step by step sesuai checklist.
4. Setiap step selesai, kasih checklist untuk dicentang.
5. Bahasa: Indonesia santai tapi jelas.

```
"""
    """
    return md


# ============================================================
# ROUTING
# ============================================================

# === 1. Belum login → login screen ===
if not st.session_state.logged_in:
    render_login_screen()
    st.stop()

# === 2. Belum pilih → menu screen ===
if st.session_state.current_page is None:
    render_menu_screen()
    st.stop()

# === 3. Sudah pilih → render halaman ===

# Top bar
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

# ⬇️⬇️⬇️ LANJUT KE BAGIAN 2 ⬇️⬇️⬇️
# ============================================================
# HALAMAN: DASHBOARD
# ============================================================
if st.session_state.current_page == "dashboard":

    # === UPLOAD DATABASE ===
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

    # === LOAD TABEL ===
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

    # === PREPARE DATA ===
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

    # === FILTER TANGGAL ===
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

    # === CASH KLERK ===
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

    # === NON-COMMERCE ===
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

    # === KPI ===
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

    # === JAM RAMAI ===
    st.markdown("---")
    st.subheader("🕐 Jam Ramai Transaksi")

    if "time_tx" in df.columns and df["time_tx"].notna().any():
        df_time = df.copy()

        def get_hour(t):
            try:
                s = str(t).strip()
                return int(s.split(":")[0]) if ":" in s else None
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

            per_jam_aktif = per_jam[per_jam["Jumlah_Transaksi"] > 0]
            if not per_jam_aktif.empty:
                jam_teramai = per_jam_aktif.loc[per_jam_aktif["Jumlah_Transaksi"].idxmax()]
                jam_tersepi = per_jam_aktif.loc[per_jam_aktif["Jumlah_Transaksi"].idxmin()]

                col_a, col_b = st.columns(2)
                with col_a:
                    st.success(
                        "🔥 Jam Teramai: "
                        + str(int(jam_teramai["jam"])).zfill(2) + ":00"
                        + " — " + str(int(jam_teramai["Jumlah_Transaksi"])) + " transaksi"
                    )
                with col_b:
                    st.warning(
                        "❄️ Jam Tersepi: "
                        + str(int(jam_tersepi["jam"])).zfill(2) + ":00"
                        + " — " + str(int(jam_tersepi["Jumlah_Transaksi"])) + " transaksi"
                    )
        else:
            st.info("Tidak ada transaksi di rentang tanggal ini.")
    else:
        st.info("Kolom time_tx tidak ditemukan.")

    # === REKAP PER KASIR ===
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

# ⬇️⬇️⬇️ LANJUT KE BAGIAN 3 ⬇️⬇️⬇️
# ============================================================
# HALAMAN: IDEA BOX
# ============================================================
elif st.session_state.current_page == "idea_box":

    st.title("💡 Idea Box")
    st.markdown("Tulis ide → auto-generate blueprint → copy ke AI lain.")
    st.markdown("---")

    # Session state
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = None

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Tambah Ide",
        "📋 Daftar Ide",
        "🗑️ Arsip",
        "⚙️ Pengaturan"
    ])

    # === TAB 1: TAMBAH IDE ===
    with tab1:
        st.markdown("### ➕ Tambah Ide Baru")

        with st.form("form_ide", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                judul = st.text_input(
                    "Judul Ide *",
                    placeholder="Contoh: Analisis Jam Ramai per Kasir"
                )
                kategori = st.selectbox(
                    "Kategori",
                    ["Analytics", "Visualisasi", "Audit", "Monitoring", "Lainnya"]
                )
                prioritas = st.selectbox(
                    "Prioritas",
                    ["Rendah", "Sedang", "Tinggi", "Urgent"]
                )

            with col2:
                estimasi = st.number_input("Estimasi (hari)", min_value=1, max_value=30, value=2)
                file_target = st.text_input("File Target", placeholder="pages/14_Fitur_Baru.py")
                catatan = st.text_area("Catatan (opsional)", placeholder="Butuh join tabel X + Y...", height=80)

            deskripsi = st.text_area(
                "Deskripsi Ide *",
                placeholder="Jelaskan sedetail mungkin apa yang kamu mau...",
                height=120
            )

            submitted = st.form_submit_button(
                "🚀 Generate Blueprint",
                type="primary",
                use_container_width=True
            )

        if submitted:
            if not judul or not deskripsi:
                st.error("❌ Judul dan Deskripsi wajib diisi!")
            else:
                ideas_data = load_ideas()
                new_id = f"idea_{len(ideas_data['ideas']) + 1:03d}_{int(datetime.now().timestamp())}"

                new_idea = {
                    "id": new_id,
                    "judul": judul,
                    "deskripsi": deskripsi,
                    "kategori": kategori,
                    "prioritas": prioritas,
                    "status": "pending",
                    "tanggal_dibuat": datetime.now().isoformat(),
                    "estimasi_hari": estimasi,
                    "file_target": [file_target] if file_target else [f"pages/{new_id}.py"],
                    "catatan": catatan,
                }

                ideas_data["ideas"].append(new_idea)
                save_ideas(ideas_data)

                st.success("✅ Ide berhasil ditambahkan!")
                st.balloons()
                st.rerun()

    # === TAB 2: DAFTAR IDE ===
    with tab2:
        ideas_data = load_ideas()

        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            filter_status = st.multiselect(
                "Filter Status",
                ["pending", "in_progress", "done"],
                default=["pending", "in_progress"]
            )
        with col_f2:
            filter_prioritas = st.multiselect(
                "Filter Prioritas",
                ["Rendah", "Sedang", "Tinggi", "Urgent"],
                default=["Rendah", "Sedang", "Tinggi", "Urgent"]
            )
        with col_f3:
            sort_by = st.selectbox("Sort", ["Terbaru", "Prioritas", "Judul"])

        filtered = [
            (i, idea) for i, idea in enumerate(ideas_data["ideas"])
            if idea["status"] in filter_status
            and idea["prioritas"] in filter_prioritas
        ]

        if sort_by == "Terbaru":
            filtered.sort(key=lambda x: x[1]["tanggal_dibuat"], reverse=True)
        elif sort_by == "Prioritas":
            urut = {"Urgent": 0, "Tinggi": 1, "Sedang": 2, "Rendah": 3}
            filtered.sort(key=lambda x: urut.get(x[1]["prioritas"], 4))
        else:
            filtered.sort(key=lambda x: x[1]["judul"].lower())

        st.markdown(f"### 📋 Daftar Ide ({len(filtered)} dari {len(ideas_data['ideas'])})")

        if not filtered:
            st.info("Tidak ada ide yang cocok dengan filter.")
        else:
            for i, idea in filtered:
                icon_pri = {"Urgent": "🔴", "Tinggi": "🟠", "Sedang": "🟡", "Rendah": "🟢"}.get(idea["prioritas"], "⚪")
                icon_stat = {"pending": "⏳", "in_progress": "🚧", "done": "✅"}.get(idea["status"], "❓")

                with st.expander(f"{icon_pri} {icon_stat} {idea['judul']} — {idea['prioritas']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**ID:** `{idea['id']}`")
                        st.write(f"**Kategori:** {idea['kategori']}")
                        st.write(f"**Status:** {idea['status']}")
                    with c2:
                        st.write(f"**Estimasi:** {idea['estimasi_hari']} hari")
                        st.write(f"**Dibuat:** {idea['tanggal_dibuat'][:10]}")
                        st.write(f"**File:** `{', '.join(idea['file_target'])}`")

                    st.markdown("**Deskripsi:**")
                    st.write(idea["deskripsi"])

                    if idea.get("catatan"):
                        st.markdown("**Catatan:**")
                        st.write(idea["catatan"])

                    md = generate_blueprint_md(idea)

                    col_a, col_b, col_c, col_d = st.columns(4)

                    with col_a:
                        st.download_button(
                            "📥 Download",
                            data=md,
                            file_name=f"{idea['id']}.md",
                            mime="text/markdown",
                            key=f"dl_{idea['id']}",
                            use_container_width=True,
                        )

                    with col_b:
                        if st.button("📋 Copy", key=f"copy_{idea['id']}", use_container_width=True):
                            st.session_state[f"show_copy_{idea['id']}"] = True

                    with col_c:
                        status_next = {"pending": "in_progress", "in_progress": "done", "done": "pending"}
                        if st.button(f"🔄 {status_next.get(idea['status'], 'pending')}", key=f"stat_{idea['id']}", use_container_width=True):
                            ideas_data["ideas"][i]["status"] = status_next.get(idea["status"], "pending")
                            save_ideas(ideas_data)
                            st.rerun()

                    with col_d:
                        if st.button("🗑️ Hapus", key=f"del_{idea['id']}", type="secondary", use_container_width=True):
                            st.session_state.confirm_delete = i

                    if st.session_state.get(f"show_copy_{idea['id']}"):
                        st.code(md, language="markdown")
                        st.info("👆 Blok teks di atas → copy → paste ke AI lain")
                        if st.button("❌ Tutup", key=f"close_copy_{idea['id']}"):
                            st.session_state[f"show_copy_{idea['id']}"] = False
                            st.rerun()

        # Konfirmasi hapus
        if st.session_state.confirm_delete is not None:
            idx = st.session_state.confirm_delete
            ideas_data = load_ideas()

            if 0 <= idx < len(ideas_data["ideas"]):
                idea = ideas_data["ideas"][idx]
                st.error("⚠️ Yakin mau hapus ide ini?")
                st.error("⚠️ Yakin mau hapus ide ini?")
                st.markdown(f"**Judul:** {idea['judul']}")
                st.markdown(f"**Kategori:** {idea['kategori']}")
                st.markdown("Ide ini akan dipindah ke **Arsip** (bisa di-restore nanti).")

                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("✅ Ya, ke Arsip", type="primary", key="yes_del", use_container_width=True):
                        hapus_ide(idx, soft=True)
                        st.session_state.confirm_delete = None
                        st.success("✅ Ide dipindah ke arsip")
                        st.rerun()
                with c2:
                    if st.button("❌ Hapus Permanen", key="perm_del", use_container_width=True):
                        hapus_ide(idx, soft=False)
                        st.session_state.confirm_delete = None
                        st.success("🗑️ Ide dihapus permanen")
                        st.rerun()
                with c3:
                    if st.button("↩️ Batal", key="cancel_del", use_container_width=True):
                        st.session_state.confirm_delete = None
                        st.rerun()

    # === TAB 3: ARSIP ===
    with tab3:
        archive_data = load_archive()

        st.markdown(f"### 🗑️ Arsip Ide ({len(archive_data['ideas'])})")
        st.caption("Ide yang dihapus bisa di-restore dari sini.")

        if not archive_data["ideas"]:
            st.info("Arsip kosong.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("♻️ Restore Semua", key="restore_all", use_container_width=True):
                    ideas_data = load_ideas()
                    for idea in archive_data["ideas"]:
                        idea.pop("tanggal_dihapus", None)
                        idea.pop("alasan", None)
                        idea["status"] = "pending"
                        ideas_data["ideas"].append(idea)
                    archive_data["ideas"] = []
                    save_ideas(ideas_data)
                    save_archive(archive_data)
                    st.success("✅ Semua ide di-restore")
                    st.rerun()

            with col_b:
                if st.button("🗑️ Kosongkan Arsip", type="secondary", key="clear_archive", use_container_width=True):
                    archive_data["ideas"] = []
                    save_archive(archive_data)
                    st.success("🗑️ Arsip dikosongkan")
                    st.rerun()

            st.markdown("---")

            for i, idea in enumerate(archive_data["ideas"]):
                with st.expander(f"📦 {idea['judul']} — {idea.get('tanggal_dihapus', 'N/A')[:10]}"):
                    st.write(f"**Alasan:** {idea.get('alasan', '-')}")
                    st.write(f"**Kategori:** {idea['kategori']}")
                    st.write(f"**Deskripsi:** {idea['deskripsi']}")

                    col_r, col_p = st.columns(2)
                    with col_r:
                        if st.button("♻️ Restore", key=f"restore_{i}", use_container_width=True):
                            restore_ide(i)
                            st.success("✅ Ide di-restore")
                            st.rerun()
                    with col_p:
                        if st.button("🗑️ Hapus Permanen", key=f"perm_{i}", type="secondary", use_container_width=True):
                            hapus_permanen(i)
                            st.success("🗑️ Dihapus permanen")
                            st.rerun()

    # === TAB 4: PENGATURAN ===
    with tab4:
        st.markdown("### ⚙️ Pengaturan")

        ideas_data = load_ideas()
        archive_data = load_archive()

        st.markdown("#### 📊 Statistik")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📋 Ide Aktif", len(ideas_data["ideas"]))
        c2.metric("🗑️ Di Arsip", len(archive_data["ideas"]))
        c3.metric("⏳ Pending", sum(1 for i in ideas_data["ideas"] if i["status"] == "pending"))
        c4.metric("✅ Done", sum(1 for i in ideas_data["ideas"] if i["status"] == "done"))

        st.markdown("---")
        st.markdown("#### 📦 Export Semua Ide")

        if ideas_data["ideas"]:
            semua_md = f"# SEMUA IDE — {len(ideas_data['ideas'])} ide aktif\n\n"
            semua_md += f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}\n\n---\n\n"
            for idea in ideas_data["ideas"]:
                semua_md += generate_blueprint_md(idea) + "\n\n---\n\n"

            st.download_button(
                "📥 Download SEMUA Ide (.md)",
                data=semua_md,
                file_name=f"semua_ide_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            st.info("Belum ada ide untuk di-export.")


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("Pustaka Struk v2.0 — Untuk orang beramin")
