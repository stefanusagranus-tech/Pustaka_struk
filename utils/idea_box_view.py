"""
idea_box_view.py — Logic render halaman Idea Box.
"""
import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from utils.ui_components import (
    render_header,
    render_section_title,
    metric_grid,
)


IDEAS_FILE = "docs/ideas.json"
ARCHIVE_FILE = "docs/ideas_archive.json"


# ============================================================
# Helper JSON
# ============================================================
def _load_json(filepath, default):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _save_json(filepath, data):
    data["last_update"] = datetime.now().isoformat()
    if "ideas" in data:
        data["total_ideas"] = len(data["ideas"])
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_ideas():
    return _load_json(IDEAS_FILE, {
        "last_update": datetime.now().isoformat(),
        "total_ideas": 0,
        "ideas": [],
    })


def load_archive():
    return _load_json(ARCHIVE_FILE, {
        "last_update": datetime.now().isoformat(),
        "total_ideas": 0,
        "ideas": [],
    })


def save_ideas(data):
    _save_json(IDEAS_FILE, data)


def save_archive(data):
    _save_json(ARCHIVE_FILE, data)


# ============================================================
# CRUD
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
# Blueprint Generator
# ============================================================
def _generate_steps(idea):
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
    steps = _generate_steps(idea)
    lines = [
        f"# BLUEPRINT: {idea['judul']}", "",
        f"**ID:** {idea['id']}",
        f"**Kategori:** {idea['kategori']}",
        f"**Prioritas:** {idea['prioritas']}",
        f"**Estimasi:** {idea['estimasi_hari']} hari",
        f"**Tanggal Dibuat:** {idea['tanggal_dibuat']}", "",
        "---", "", "## Deskripsi", "", str(idea['deskripsi']), "",
        "---", "", "## File Target", "",
    ]
    for f in idea['file_target']:
        lines.append(f"- `{f}`")
    lines += ["", "---", "", "## Step-by-Step", ""]
    for i, step in enumerate(steps, 1):
        lines.append(f"{i}. [ ] {step}")
    lines += ["", "---", "", "## Catatan", "", str(idea.get('catatan', '-'))]
    return "\n".join(lines)


# ============================================================
# MAIN RENDER
# ============================================================
def render_idea_box():
    render_header(
        "Idea Box",
        "Tulis ide → auto-generate blueprint → copy ke AI lain",
        icon="💡",
    )

    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = None

    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Tambah Ide", "📋 Daftar Ide", "🗑️ Arsip", "⚙️ Pengaturan",
    ])

    # ---------- TAB 1: TAMBAH ----------
    with tab1:
        with st.form("form_ide", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                judul = st.text_input("Judul Ide *")
                kategori = st.selectbox(
                    "Kategori",
                    ["Analytics", "Visualisasi", "Audit", "Monitoring", "Lainnya"],
                )
                prioritas = st.selectbox(
                    "Prioritas", ["Rendah", "Sedang", "Tinggi", "Urgent"]
                )
            with col2:
                estimasi = st.number_input(
                    "Estimasi (hari)", min_value=1, max_value=30, value=2
                )
                file_target = st.text_input(
                    "File Target", placeholder="pages/14_Fitur_Baru.py"
                )
                catatan = st.text_area("Catatan (opsional)", height=80)
            deskripsi = st.text_area("Deskripsi Ide *", height=120)
            submitted = st.form_submit_button(
                "🚀 Generate Blueprint", type="primary", use_container_width=True
            )

        if submitted:
            if not judul or not deskripsi:
                st.error("❌ Judul dan Deskripsi wajib diisi!")
            else:
                ideas_data = load_ideas()
                new_id = f"idea_{len(ideas_data['ideas']) + 1:03d}_{int(datetime.now().timestamp())}"
                new_idea = {
                    "id": new_id, "judul": judul, "deskripsi": deskripsi,
                    "kategori": kategori, "prioritas": prioritas, "status": "pending",
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

    # ---------- TAB 2: DAFTAR ----------
    with tab2:
        ideas_data = load_ideas()
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            filter_status = st.multiselect(
                "Status", ["pending", "in_progress", "done"],
                default=["pending", "in_progress"],
            )
        with col_f2:
            filter_prioritas = st.multiselect(
                "Prioritas", ["Rendah", "Sedang", "Tinggi", "Urgent"],
                default=["Rendah", "Sedang", "Tinggi", "Urgent"],
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

        render_section_title(f"Daftar Ide ({len(filtered)})", "📋")
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
                        st.download_button(
                            "📥 Download", data=md,
                            file_name=f"{idea['id']}.md", mime="text/markdown",
                            key=f"dl_{idea['id']}", use_container_width=True,
                        )
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

    # ---------- TAB 3: ARSIP ----------
    with tab3:
        archive_data = load_archive()
        render_section_title(f"Arsip ({len(archive_data['ideas'])})", "🗑️")
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

    # ---------- TAB 4: PENGATURAN ----------
    with tab4:
        render_section_title("Pengaturan", "⚙️")
        ideas_data = load_ideas()
        archive_data = load_archive()
        metric_grid([
            {"label": "Aktif", "value": str(len(ideas_data["ideas"])), "variant": "accent"},
            {"label": "Arsip", "value": str(len(archive_data["ideas"]))},
            {"label": "Pending", "value": str(sum(1 for i in ideas_data["ideas"] if i["status"] == "pending")), "variant": "warning"},
            {"label": "Done", "value": str(sum(1 for i in ideas_data["ideas"] if i["status"] == "done")), "variant": "success"},
        ], cols=4)
