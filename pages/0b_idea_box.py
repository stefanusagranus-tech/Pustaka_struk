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
