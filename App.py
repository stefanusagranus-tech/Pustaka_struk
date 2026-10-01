"""
App.py — Pustaka Struk Main App
Include: Login + Menu (3 tombol) + Dashboard + Idea Box + Manage PLU.
"""
import streamlit as st
import pandas as pd
import os
import shutil
import json
import sys
from datetime import datetime, date
from pathlib import Path

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
from utils.plu_loader import (
    KATEGORI,
    list_plu_files,
    save_plu_csv,
    delete_plu_file,
    load_plu_from_file,
    load_plu_by_date,
    get_stats,
)

# ============================================================
# SETUP
# ============================================================
setup_anonim_page("Pustaka Struk", "📦")
apply_nav_style()

init_auth_state()

# ============================================================
# PATH FILE
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
# GENERATE BLUEPRINT
# ============================================================
def generate_steps(idea):
    return [
        f"Analisis kebutuhan: {idea['judul']}",
        "Baca tabel terkait di SQLite",
        f"Bikin query pandas untuk {idea['deskripsi'][:50]}...",
        f"Bikin file: {', '.join(idea['file_target'])}",
        "Bikin visualisasi (chart/table)",
        "Tambah filter interaktif",
        "Tambah tombol download CSV",
        "Uji dengan data",
        "Commit + push ke GitHub",
        "Update progress.json",
    ]


def generate_blueprint_md(idea):
    steps = generate_steps(idea)
    lines = []
    lines.append("# BLUEPRINT: " + str(idea['judul']))
    lines.append("")
    lines.append("**ID:** " + str(idea['id']))
    lines.append("**Kategori:** " + str(idea['kategori']))
    lines.append("**Prioritas:** " + str(idea['prioritas']))
    lines.append("**Estimasi:** " + str(idea['estimasi_hari']) + " hari")
    lines.append("**Tanggal Dibuat:** " + str(idea['tanggal_dibuat']))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Deskripsi")
    lines.append("")
    lines.append(str(idea['deskripsi']))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## File Target")
    lines.append("")
    for f in idea['file_target']:
        lines.append("- `" + str(f) + "`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Step-by-Step")
    lines.append("")
    for i, step in enumerate(steps, 1):
        lines.append(str(i) + ". [ ] " + str(step))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Catatan")
    lines.append("")
    lines.append(str(idea.get('catatan', '-')))
    return "\n".join(lines)

# ⬇️⬇️⬇️ LANJUT KE BAGIAN 2 ⬇️⬇️⬇️

# ============================================================
# ROUTING
# ============================================================
if not st.session_state.logged_in:
    render_login_screen()
    st.stop()

if st.session_state.current_page is None:
    render_menu_screen()
    st.stop()

# Top bar
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    page_map = {
        "dashboard": "📊 Dashboard",
        "idea_box": "💡 Idea Box",
        "manage_plu": "📋 Manage PLU",
    }
    page_name = page_map.get(st.session_state.current_page, "📄 Halaman")
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

    # === PREPARE ===
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

# ⬇️⬇️⬇️ LANJUT KE BAGIAN 3 ⬇️⬇️⬇️

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

    # === MENU HALAMAN ANALISIS ===
    st.markdown("---")
    st.markdown("### 📂 Halaman Analisis")
    st.caption("Database udah ke-load — tap tombol di bawah buat analisis")

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        if st.button("📊 1 PSM per PLU", use_container_width=True, key="dash_nav_psm"):
            st.switch_page("pages/1_PSM_per_PLU.py")
        if st.button("📦 3 Topup Flaz", use_container_width=True, key="dash_nav_topup"):
            st.switch_page("pages/5_Topup_Flaz.py")

    with col_a2:
        if st.button("🎁 2 SG per Paket", use_container_width=True, key="dash_nav_sg"):
            st.switch_page("pages/2_SG_per_Paket.py")
        if st.button("🧾 4 Cek Struk", use_container_width=True, key="dash_nav_struk"):
            st.switch_page("pages/3_struk_Suger.py")

    st.markdown("---")
    st.markdown("### 🔧 Tools")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        if st.button("🔍 Cek Struk Detail", use_container_width=True, key="dash_nav_cek_struk"):
            st.switch_page("pages/7_Cek_Struk_Detail.py")

    with col_t2:
        if st.button("❌ Void Transaksi", use_container_width=True, key="dash_nav_void"):
            st.switch_page("pages/6_Cek_Struk_Void.py")


# ============================================================
# HALAMAN: IDEA BOX
# ============================================================
elif st.session_state.current_page == "idea_box":

    st.title("💡 Idea Box")
    st.markdown("Tulis ide → auto-generate blueprint → copy ke AI lain.")
    st.markdown("---")

    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = None

    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Tambah Ide",
        "📋 Daftar Ide",
        "🗑️ Arsip",
        "⚙️ Pengaturan"
    ])

    # === TAB 1: TAMBAH ===
    with tab1:
        st.markdown("### ➕ Tambah Ide Baru")

        with st.form("form_ide", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                judul = st.text_input("Judul Ide *")
                kategori = st.selectbox("Kategori", ["Analytics", "Visualisasi", "Audit", "Monitoring", "Lainnya"])
                prioritas = st.selectbox("Prioritas", ["Rendah", "Sedang", "Tinggi", "Urgent"])

            with col2:
                estimasi = st.number_input("Estimasi (hari)", min_value=1, max_value=30, value=2)
                file_target = st.text_input("File Target", placeholder="pages/14_Fitur_Baru.py")
                catatan = st.text_area("Catatan (opsional)", height=80)

            deskripsi = st.text_area("Deskripsi Ide *", height=120)

            submitted = st.form_submit_button("🚀 Generate Blueprint", type="primary", use_container_width=True)

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

    # === TAB 2: DAFTAR ===
    with tab2:
        ideas_data = load_ideas()

        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            filter_status = st.multiselect("Status", ["pending", "in_progress", "done"], default=["pending", "in_progress"])
        with col_f2:
            filter_prioritas = st.multiselect("Prioritas", ["Rendah", "Sedang", "Tinggi", "Urgent"], default=["Rendah", "Sedang", "Tinggi", "Urgent"])
        with col_f3:
            sort_by = st.selectbox("Sort", ["Terbaru", "Prioritas", "Judul"])

        filtered = [
            (i, idea) for i, idea in enumerate(ideas_data["ideas"])
            if idea["status"] in filter_status and idea["prioritas"] in filter_prioritas
        ]

        if sort_by == "Terbaru":
            filtered.sort(key=lambda x: x[1]["tanggal_dibuat"], reverse=True)
        elif sort_by == "Prioritas":
            urut = {"Urgent": 0, "Tinggi": 1, "Sedang": 2, "Rendah": 3}
            filtered.sort(key=lambda x: urut.get(x[1]["prioritas"], 4))
        else:
            filtered.sort(key=lambda x: x[1]["judul"].lower())

        st.markdown(f"### 📋 Daftar Ide ({len(filtered)})")

        if not filtered:
            st.info("Tidak ada ide.")
        else:
            for i, idea in filtered:
                icon_pri = {"Urgent": "🔴", "Tinggi": "🟠", "Sedang": "🟡", "Rendah": "🟢"}.get(idea["prioritas"], "⚪")
                icon_stat = {"pending": "⏳", "in_progress": "🚧", "done": "✅"}.get(idea["status"], "❓")

                with st.expander(f"{icon_pri} {icon_stat} {idea['judul']}"):
                    st.write(f"**ID:** `{idea['id']}`")
                    st.write(f"**Kategori:** {idea['kategori']}")
                    st.write(f"**Status:** {idea['status']}")
                    st.markdown("**Deskripsi:**")
                    st.write(idea["deskripsi"])

                    md = generate_blueprint_md(idea)

                    col_a, col_b, col_c, col_d = st.columns(4)

                    with col_a:
                        st.download_button("📥 Download", data=md, file_name=f"{idea['id']}.md", mime="text/markdown", key=f"dl_{idea['id']}", use_container_width=True)

                    with col_b:
                        if st.button("📋 Copy", key=f"copy_{idea['id']}", use_container_width=True):
                            st.session_state[f"show_copy_{idea['id']}"] = True

                    with col_c:
                        status_next = {"pending": "in_progress", "in_progress": "done", "done": "pending"}
                        if st.button("🔄", key=f"stat_{idea['id']}", use_container_width=True):
                            ideas_data["ideas"][i]["status"] = status_next.get(idea["status"], "pending")
                            save_ideas(ideas_data)
                            st.rerun()

                    with col_d:
                        if st.button("🗑️", key=f"del_{idea['id']}", type="secondary", use_container_width=True):
                            st.session_state.confirm_delete = i

                    if st.session_state.get(f"show_copy_{idea['id']}"):
                        st.code(md, language="markdown")
                        st.info("👆 Copy → paste ke AI lain")
                        if st.button("❌ Tutup", key=f"close_copy_{idea['id']}"):
                            st.session_state[f"show_copy_{idea['id']}"] = False
                            st.rerun()

        if st.session_state.confirm_delete is not None:
            idx = st.session_state.confirm_delete
            ideas_data = load_ideas()
            if 0 <= idx < len(ideas_data["ideas"]):
                idea = ideas_data["ideas"][idx]
                st.error("⚠️ Yakin hapus ide ini?")
                st.markdown(f"**Judul:** {idea['judul']}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("✅ Ke Arsip", type="primary", key="yes_del", use_container_width=True):
                        hapus_ide(idx, soft=True)
                        st.session_state.confirm_delete = None
                        st.rerun()
                with c2:
                    if st.button("❌ Permanen", key="perm_del", use_container_width=True):
                        hapus_ide(idx, soft=False)
                        st.session_state.confirm_delete = None
                        st.rerun()
                with c3:
                    if st.button("↩️ Batal", key="cancel_del", use_container_width=True):
                        st.session_state.confirm_delete = None
                        st.rerun()

    # === TAB 3: ARSIP ===
    with tab3:
        archive_data = load_archive()

        st.markdown(f"### 🗑️ Arsip ({len(archive_data['ideas'])})")

        if not archive_data["ideas"]:
            st.info("Arsip kosong.")
        else:
            for i, idea in enumerate(archive_data["ideas"]):
                with st.expander(f"📦 {idea['judul']}"):
                    st.write(f"**Deskripsi:** {idea['deskripsi']}")
                    col_r, col_p = st.columns(2)
                    with col_r:
                        if st.button("♻️ Restore", key=f"restore_{i}", use_container_width=True):
                            restore_ide(i)
                            st.rerun()
                    with col_p:
                        if st.button("🗑️ Permanen", key=f"perm_{i}", type="secondary", use_container_width=True):
                            hapus_permanen(i)
                            st.rerun()

    # === TAB 4: PENGATURAN ===
    with tab4:
        st.markdown("### ⚙️ Pengaturan")

        ideas_data = load_ideas()
        archive_data = load_archive()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📋 Aktif", len(ideas_data["ideas"]))
        c2.metric("🗑️ Arsip", len(archive_data["ideas"]))
        c3.metric("⏳ Pending", sum(1 for i in ideas_data["ideas"] if i["status"] == "pending"))
        c4.metric("✅ Done", sum(1 for i in ideas_data["ideas"] if i["status"] == "done"))

# ⬇️⬇️⬇️ LANJUT KE BAGIAN 4 ⬇️⬇️⬇️


# ============================================================
# HALAMAN: MANAGE PLU
# ============================================================
elif st.session_state.current_page == "manage_plu":

    st.title("📋 Manage PLU")
    st.markdown("Kelola PLU untuk 4 kategori: **PSM, SG, PWP, Suger**.")

    # === STATISTIK ===
    st.markdown("---")
    st.markdown("### 📊 Statistik")

    stats = get_stats()
    cols = st.columns(4)

    for i, (kat, info) in enumerate(stats.items()):
        with cols[i]:
            st.metric(
                f"{info['icon']} {info['nama']}",
                f"{info['jumlah_file']} file",
                f"{info['total_plu']} PLU",
            )

    # === TABS ===
    tab1, tab2, tab3 = st.tabs([
        "📤 Upload PLU",
        "📂 Daftar File",
        "🔍 Cek PLU Aktif",
    ])

    # === TAB 1: UPLOAD ===
    with tab1:
        st.markdown("### 📤 Upload File PLU")

        st.info(
            "Format CSV harus punya kolom **PLU**. "
            "Kolom lain (Desc, Mekanisme, Brand, Kat) optional."
        )

        with st.form("form_upload_plu"):
            kategori_pilihan = st.selectbox(
                "Kategori PLU:",
                options=list(KATEGORI.keys()),
                format_func=lambda x: f"{KATEGORI[x]['icon']} {KATEGORI[x]['nama']}",
                key="upload_kategori",
            )

            uploaded = st.file_uploader(
                "Pilih file CSV",
                type=["csv"],
                key="plu_csv_upload",
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                tahun = st.number_input("Tahun", min_value=2020, max_value=2100, value=date.today().year)

            with col2:
                bulan = st.number_input("Bulan", min_value=1, max_value=12, value=date.today().month)

            with col3:
                tgl_range = st.text_input("Rentang (contoh: 01_15)", value="01_15")

            submit = st.form_submit_button("🚀 Upload & Simpan", type="primary", use_container_width=True)

        if submit:
            if not uploaded:
                st.error("❌ Pilih file CSV dulu.")
            else:
                try:
                    parts = tgl_range.strip().split("_")
                    if len(parts) != 2:
                        raise ValueError
                    tgl_awal = int(parts[0])
                    tgl_akhir = int(parts[1])
                except (ValueError, IndexError):
                    st.error("❌ Format rentang salah. Contoh: `01_15`")
                    st.stop()

                success, message, filepath = save_plu_csv(
                    uploaded, kategori_pilihan, tahun, bulan, tgl_awal, tgl_akhir
                )

                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")

    # === TAB 2: DAFTAR FILE ===
    with tab2:
        st.markdown("### 📂 Daftar File PLU")

        kategori_lihat = st.selectbox(
            "Pilih kategori:",
            options=list(KATEGORI.keys()),
            format_func=lambda x: f"{KATEGORI[x]['icon']} {KATEGORI[x]['nama']}",
            key="lihat_kategori",
        )

        files = list_plu_files(kategori_lihat)

        if not files:
            st.info(f"Belum ada file PLU untuk **{KATEGORI[kategori_lihat]['nama']}**.")
        else:
            st.markdown(f"**Total {len(files)} file**")

            df_files = pd.DataFrame([
                {
                    "Periode": f["periode_label"],
                    "File": f["filename"],
                    "Jumlah PLU": len(load_plu_from_file(f["path"])),
                }
                for f in files
            ])

            st.dataframe(df_files, use_container_width=True, hide_index=True)

# ⬇️⬇️⬇️ LANJUT KE BAGIAN 5 ⬇️⬇️⬇️

            st.markdown("---")
            st.markdown("### 🗑️ Hapus File")

            file_options = [f["filename"] for f in files]
            to_delete = st.selectbox(
                "Pilih file untuk dihapus:",
                file_options,
                key="plu_delete_select",
            )

            if st.button("🗑️ Hapus File", type="secondary"):
                if delete_plu_file(kategori_lihat, to_delete):
                    st.success(f"✅ File {to_delete} dihapus.")
                    st.rerun()
                else:
                    st.error("❌ Gagal hapus.")

            st.markdown("---")
            st.markdown("### 👁️ Preview File")

            preview_file = st.selectbox(
                "Pilih file:",
                file_options,
                key="plu_preview_select",
            )

            preview_info = next((f for f in files if f["filename"] == preview_file), None)

            if preview_info:
                plu_list = load_plu_from_file(preview_info["path"])

                st.markdown(f"**Periode:** {preview_info['periode_label']}")
                st.markdown(f"**Jumlah PLU:** {len(plu_list)}")

                if plu_list:
                    df_preview = pd.DataFrame(plu_list[:50])
                    st.dataframe(df_preview, use_container_width=True, hide_index=True)

                    if len(plu_list) > 50:
                        st.caption(f"... dan {len(plu_list) - 50} PLU lainnya")

    # === TAB 3: CEK PLU AKTIF ===
    with tab3:
        st.markdown("### 🔍 Cek PLU Aktif")

        col1, col2 = st.columns(2)

        with col1:
            kategori_cek = st.selectbox(
                "Kategori:",
                options=list(KATEGORI.keys()),
                format_func=lambda x: f"{KATEGORI[x]['icon']} {KATEGORI[x]['nama']}",
                key="cek_kategori",
            )

        with col2:
            tgl_cek = st.date_input(
                "Tanggal:",
                value=date.today(),
                key="plu_cek_tgl",
            )

        plu_list, file_info = load_plu_by_date(kategori_cek, tgl_cek)

        if file_info is None:
            st.warning(
                f"⚠️ Tidak ada file PLU **{KATEGORI[kategori_cek]['nama']}** "
                f"untuk tanggal {tgl_cek}."
            )
        else:
            st.success(
                f"✅ Periode: **{file_info['periode_label']}** "
                f"({len(plu_list)} PLU)"
            )

            if plu_list:
                df_plu = pd.DataFrame(plu_list)

                keyword = st.text_input(
                    "🔎 Cari PLU/Nama:",
                    placeholder="Contoh: 434304 atau LEMONILO",
                )

                if keyword:
                    keyword = str(keyword).strip().lower()
                    nama_col = df_plu.get("nama", pd.Series([""] * len(df_plu)))
                    mask = (
                        df_plu["plu"].astype(str).str.contains(keyword, na=False)
                        | nama_col.astype(str).str.lower().str.contains(keyword, na=False)
                    )
                    df_plu = df_plu[mask]
                    st.caption(f"Ditemukan {len(df_plu)} PLU.")

                st.dataframe(df_plu, use_container_width=True, hide_index=True)

                st.download_button(
                    f"📥 Download PLU {KATEGORI[kategori_cek]['nama']} ({tgl_cek})",
                    data=df_plu.to_csv(index=False).encode("utf-8"),
                    file_name=f"plu_{kategori_cek}_{tgl_cek}.csv",
                    mime="text/csv",
                )


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("Pustaka Struk v2.0 — Internal use only")
