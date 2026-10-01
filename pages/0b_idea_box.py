"""
💡 Idea Box — Tulis ide → auto-generate blueprint → copy ke AI.
Fitur:
- Tambah ide → auto-generate blueprint
- Hapus ide dengan konfirmasi (soft/hard delete)
- Arsip ide
- Filter & sort
- Export semua ide
"""
import streamlit as st
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Tambah path root ke sys.path biar bisa import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style

# ============================================================
# SETUP ANONIM
# ============================================================
setup_anonim_page("💡 Idea Box", "💡")
apply_nav_style()

# ============================================================
# PATH FILE
# ============================================================
IDEAS_FILE = "docs/ideas.json"
ARCHIVE_FILE = "docs/ideas_archive.json"


# ============================================================
# FUNGSI JSON
# ============================================================
def load_json(filepath, default):
    """Load JSON, return default kalau file gak ada."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(filepath, data):
    """Save JSON + auto-update timestamp."""
    data["last_update"] = datetime.now().isoformat()
    if "ideas" in data:
        data["total_ideas"] = len(data["ideas"])
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_ideas():
    """Load daftar ide aktif."""
    return load_json(IDEAS_FILE, {
        "last_update": datetime.now().isoformat(),
        "total_ideas": 0,
        "ideas": []
    })


def load_archive():
    """Load arsip ide."""
    return load_json(ARCHIVE_FILE, {
        "last_update": datetime.now().isoformat(),
        "total_ideas": 0,
        "ideas": []
    })


def save_ideas(data):
    save_json(IDEAS_FILE, data)


def save_archive(data):
    save_json(ARCHIVE_FILE, data)


# ============================================================
# FUNGSI HAPUS / RESTORE
# ============================================================
def hapus_ide(index, soft=True):
    """Hapus ide — soft delete (arsip) atau hard delete."""
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
    """Restore ide dari arsip."""
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
    """Hapus permanen dari arsip."""
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
    """Generate step-by-step dari ide."""
    return [
        f"Analisis kebutuhan: {idea['judul']}",
        "Baca tabel terkait di SQLite",
        f"Bikin query pandas untuk {idea['deskripsi'].lower()[:50]}...",
        f"Bikin file: {', '.join(idea['file_target'])}",
        "Bikin visualisasi (chart/table)",
        "Tambah filter interaktif (date, kasir, dll)",
        "Tambah tombol download CSV",
        "Uji dengan data 27/09/2026",
        "Commit + push ke GitHub",
        "Update progress.json",
    ]


def generate_blueprint_md(idea):
    """Generate blueprint markdown siap kirim ke AI."""
    steps = generate_steps(idea)

    md = f"""# 🎯 BLUEPRINT: {idea['judul']}

**ID:** {idea['id']}
**Kategori:** {idea['kategori']}
**Prioritas:** {idea['prioritas']}
**Estimasi:** {idea['estimasi_hari']} hari
**Tanggal Dibuat:** {idea['tanggal_dibuat']}

---

## 📖 Deskripsi

{idea['deskripsi']}

---

## 🎯 Tujuan

Bikin fitur/halaman baru di proyek Pustaka Struk (Dashboard POS Alfamart)
untuk **{idea['judul'].lower()}**.

---

## 📁 File Target

{chr(10).join(f'- `{f}`' for f in idea['file_target'])}

---

## 📋 Step-by-Step

"""
    for i, step in enumerate(steps, 1):
        md += f"{i}. [ ] {step}\n"

    md += f"""

---

## 📊 Sumber Data

Tabel SQLite yang mungkin dipakai:
- `tx_tsale` (header penjualan)
- `tx_trans` (detail item)
- `log_receipt_prn` (data struk)
- `log_cashier` (data kasir)

*Sesuaikan dengan kebutuhan.*

---

## 🎨 Spesifikasi Output

- Halaman Streamlit baru di `pages/`
- Import `utils.common` untuk load data
- Import `utils.anonim` untuk setup anonim
- Pakai `@st.cache_data` untuk optimasi
- Ada KPI cards di atas
- Ada chart (bar/line/pie) di tengah
- Ada tabel detail di bawah
- Ada tombol download CSV
- Ada `render_nav_universal("id_halaman")` di bawah

---

## 🧪 Testing

- [ ] Uji dengan data 27/09/2026
- [ ] Cek performa (loading < 3 detik)
- [ ] Cek responsif di HP
- [ ] Cek error handling

---

## 📝 Catatan

{idea.get('catatan', '-')}

---

## 🤖 INSTRUKSI UNTUK AI


# ============================================================
# SESSION STATE
# ============================================================
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None
if "confirm_bulk" not in st.session_state:
    st.session_state.confirm_bulk = False


# ============================================================
# HEADER
# ============================================================
st.title("💡 Idea Box")
st.markdown("Tulis ide → auto-generate blueprint → copy ke AI lain.")
st.markdown("---")


# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Tambah Ide",
    "📋 Daftar Ide",
    "🗑️ Arsip",
    "⚙️ Pengaturan"
])


# ============================================================
# TAB 1: TAMBAH IDE
# ============================================================
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
            estimasi = st.number_input(
                "Estimasi (hari)",
                min_value=1, max_value=30, value=2
            )
            file_target = st.text_input(
                "File Target",
                placeholder="pages/14_Fitur_Baru.py"
            )
            catatan = st.text_area(
                "Catatan (opsional)",
                placeholder="Butuh join tabel X + Y...",
                height=100
            )

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
                "catatan": catatan
            }

            ideas_data["ideas"].append(new_idea)
            save_ideas(ideas_data)

            st.success(f"✅ Ide berhasil ditambahkan!")
            st.balloons()
            st.rerun()


# ============================================================
# TAB 2: DAFTAR IDE
# ============================================================
with tab2:
    ideas_data = load_ideas()

    # Filter
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

    # Apply filter
    filtered = [
        (i, idea) for i, idea in enumerate(ideas_data["ideas"])
        if idea["status"] in filter_status
        and idea["prioritas"] in filter_prioritas
    ]

    # Sort
    if sort_by == "Terbaru":
        filtered.sort(key=lambda x: x[1]["tanggal_dibuat"], reverse=True)
    elif sort_by == "Prioritas":
        urut = {"Urgent": 0, "Tinggi": 1, "Sedang": 2, "Rendah": 3}
        filtered.sort(key=lambda x: urut.get(x[1]["prioritas"], 4))
    elif sort_by == "Judul":
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

                # Tombol aksi
                col_a, col_b, col_c, col_d = st.columns(4)

                with col_a:
                    st.download_button(
                        "📥 Download",
                        data=md,
                        file_name=f"{idea['id']}.md",
                        mime="text/markdown",
                        key=f"dl_{idea['id']}",
                        use_container_width=True
                    )

                with col_b:
                    if st.button("📋 Copy", key=f"copy_{idea['id']}", use_container_width=True):
                        st.session_state[f"show_copy_{idea['id']}"] = True

                with col_c:
                    status_next = {
                        "pending": "in_progress",
                        "in_progress": "done",
                        "done": "pending"
                    }
                    if st.button(f"🔄 {status_next.get(idea['status'], 'pending')}", key=f"stat_{idea['id']}", use_container_width=True):
                        ideas_data["ideas"][i]["status"] = status_next.get(idea["status"], "pending")
                        save_ideas(ideas_data)
                        st.rerun()

                with col_d:
                    if st.button("🗑️ Hapus", key=f"del_{idea['id']}", type="secondary", use_container_width=True):
                        st.session_state.confirm_delete = i

                # Show copy text
                if st.session_state.get(f"show_copy_{idea['id']}"):
                    st.code(md, language="markdown")
                    st.info("👆 Blok teks di atas → copy → paste ke AI lain")
                    if st.button("❌ Tutup", key=f"close_copy_{idea['id']}"):
                        st.session_state[f"show_copy_{idea['id']}"] = False
                        st.rerun()

    # ============================================================
    # KONFIRMASI HAPUS
    # ============================================================
    if st.session_state.confirm_delete is not None:
        idx = st.session_state.confirm_delete
        ideas_data = load_ideas()

        if 0 <= idx < len(ideas_data["ideas"]):
            idea = ideas_data["ideas"][idx]

            st.error(f"⚠️ **Yakin mau hapus ide ini?**")
            st.markdown(f"""
            **Judul:** {idea['judul']}
            **Kategori:** {idea['kategori']}
            **Prioritas:** {idea['prioritas']}

            Ide ini akan dipindah ke **🗑️ Arsip** (bisa di-restore nanti).
            """)

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


# ============================================================
# TAB 3: ARSIP
# ============================================================
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
                st.write(f"**Prioritas:** {idea['prioritas']}")
                st.write(f"**Deskripsi:** {idea['deskripsi']}")

                col_r, col_p = st.columns(2)
                with col_r:
                    if st.button(f"♻️ Restore", key=f"restore_{i}", use_container_width=True):
                        restore_ide(i)
                        st.success("✅ Ide di-restore")
                        st.rerun()
                with col_p:
                    if st.button(f"🗑️ Hapus Permanen", key=f"perm_{i}", type="secondary", use_container_width=True):
                        hapus_permanen(i)
                        st.success("🗑️ Dihapus permanen")
                        st.rerun()


# ============================================================
# TAB 4: PENGATURAN
# ============================================================
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
        semua_md = f"# 📦 SEMUA IDE — {len(ideas_data['ideas'])} ide aktif\n\n"
        semua_md += f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}\n\n---\n\n"
        semua_md += "## 🟢 IDE AKTIF\n\n"
        for idea in ideas_data["ideas"]:
            semua_md += generate_blueprint_md(idea) + "\n\n---\n\n"

        st.download_button(
            "📥 Download SEMUA Ide (.md)",
            data=semua_md,
            file_name=f"semua_ide_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    else:
        st.info("Belum ada ide untuk di-export.")


# ============================================================
# NAVIGASI UNIVERSAL
# ============================================================
render_nav_universal("idea")
