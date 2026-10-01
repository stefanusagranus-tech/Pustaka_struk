"""
scripts/check_progress.py
Auto-scan progress proyek Pustaka Struk.

Fitur:
- Scan folder pages/ + utils/ + scripts/
- Bandingkan dengan progress.json
- Update status fase otomatis
- Print report + tulis ke PROGRESS_REPORT.md

Cara pakai:
    python scripts/check_progress.py
    python scripts/check_progress.py --report    # detail lengkap
    python scripts/check_progress.py --json      # output JSON
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path


# ============================================================
# KONFIGURASI
# ============================================================
PROGRESS_FILE = "docs/progress.json"
REPORT_FILE = "docs/PROGRESS_REPORT.md"
REPO_ROOT = Path(__file__).parent.parent


# ============================================================
# DEFINISI FASE (sesuai blueprint)
# ============================================================
FASE_DEFINITION = {
    "0_setup": {
        "nama": "Setup & Refactor",
        "deskripsi": "Bikin folder components/, refactor utils/",
        "file_penanda": [
            "utils/anonim.py",
            "utils/common.py",
        ],
        "estimasi_hari": 1,
    },
    "1_fix_app": {
        "nama": "Fix App.py & Anonim",
        "deskripsi": "Perbaiki bug + setup anonim + navigasi",
        "file_penanda": [
            "App.py",
            "utils/anonim.py",
        ],
        "estimasi_hari": 2,
    },
    "2_nav": {
        "nama": "Navigasi Custom",
        "deskripsi": "Tombol navigasi di semua halaman",
        "file_penanda": [
            "pages/0_Home.py",
        ],
        "estimasi_hari": 1,
    },
    "3_idea_box": {
        "nama": "Idea Box",
        "deskripsi": "Fitur tulis ide + auto-generate blueprint",
        "file_penanda": [
            "pages/0b_Idea_Box.py",
        ],
        "estimasi_hari": 2,
    },
    "4_progress_tracker": {
        "nama": "Progress Tracker",
        "deskripsi": "Auto-scan progress + dashboard",
        "file_penanda": [
            "scripts/check_progress.py",
            "docs/progress.json",
        ],
        "estimasi_hari": 1,
    },
    "5_m1_transaction": {
        "nama": "M1 Deep Transaction",
        "deskripsi": "Analisis transaksi mendalam",
        "file_penanda": ["pages/7_Transaction_Deep.py"],
        "estimasi_hari": 3,
    },
    "6_m2_promo": {
        "nama": "M2 Promo Intelligence",
        "deskripsi": "Analisis promo",
        "file_penanda": ["pages/8_Promo_Analytics.py"],
        "estimasi_hari": 3,
    },
    "7_m3_payment": {
        "nama": "M3 Payment & Wallet",
        "deskripsi": "Analisis pembayaran",
        "file_penanda": ["pages/9_Payment_Analytics.py"],
        "estimasi_hari": 2,
    },
    "8_m4_customer": {
        "nama": "M4 Customer Analytics",
        "deskripsi": "Analisis member",
        "file_penanda": ["pages/10_Customer_Analytics.py"],
        "estimasi_hari": 2,
    },
    "9_m5_kasir": {
        "nama": "M5 Kasir & Ops",
        "deskripsi": "Analisis kasir",
        "file_penanda": ["pages/11_Kasir_Ops.py"],
        "estimasi_hari": 2,
    },
    "10_m6_print": {
        "nama": "M6 Print Audit",
        "deskripsi": "Audit printing",
        "file_penanda": ["pages/12_Print_Audit.py"],
        "estimasi_hari": 1,
    },
    "11_m7_monitor": {
        "nama": "M7 System Monitor",
        "deskripsi": "Monitoring sistem",
        "file_penanda": ["pages/13_System_Health.py"],
        "estimasi_hari": 2,
    },
    "12_docs": {
        "nama": "Dokumentasi",
        "deskripsi": "README + user guide",
        "file_penanda": ["README.md"],
        "estimasi_hari": 1,
    },
    "13_deploy": {
        "nama": "Deploy Final",
        "deskripsi": "Push + Streamlit Cloud + uji",
        "file_penanda": ["docs/DEPLOY_SUCCESS.md"],
        "estimasi_hari": 1,
    },
}


# ============================================================
# FUNGSI UTILS
# ============================================================
def load_progress():
    """Load progress.json. Kalau gak ada, bikin default."""
    if not os.path.exists(PROGRESS_FILE):
        return {
            "project": "Pustaka Struk",
            "version": "2.0",
            "last_update": datetime.now().isoformat(),
            "total_fase": len(FASE_DEFINITION),
            "fase": {},
        }
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {
            "project": "Pustaka Struk",
            "version": "2.0",
            "last_update": datetime.now().isoformat(),
            "total_fase": len(FASE_DEFINITION),
            "fase": {},
        }


def save_progress(data):
    """Save progress.json."""
    data["last_update"] = datetime.now().isoformat()
    data["total_fase"] = len(data.get("fase", {}))
    Path(PROGRESS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def check_file_exists(relative_path):
    """Cek apakah file ada di repo."""
    return (REPO_ROOT / relative_path).exists()


def check_fase_status(fase_data):
    """Cek apakah fase selesai (semua file_penanda ada)."""
    files = fase_data.get("file_penanda", [])
    if not files:
        return False
    return all(check_file_exists(f) for f in files)


def get_file_details(fase_data):
    """Return detail: file mana yang ada / gak ada."""
    details = []
    for f in fase_data.get("file_penanda", []):
        exists = check_file_exists(f)
        details.append({
            "file": f,
            "exists": exists,
            "icon": "✅" if exists else "❌",
        })
    return details


# ============================================================
# CORE
# ============================================================
def scan_and_update():
    """Scan semua fase + update progress.json."""
    progress = load_progress()

    # Sync fase dengan FASE_DEFINITION
    for key, fase_def in FASE_DEFINITION.items():
        if key not in progress.get("fase", {}):
            progress["fase"][key] = {
                **fase_def,
                "status": False,
                "tanggal_selesai": None,
            }
        else:
            # Update nama & deskripsi (kalau berubah)
            progress["fase"][key]["nama"] = fase_def["nama"]
            progress["fase"][key]["deskripsi"] = fase_def["deskripsi"]
            progress["fase"][key]["file_penanda"] = fase_def["file_penanda"]
            progress["fase"][key]["estimasi_hari"] = fase_def["estimasi_hari"]

    # Cek status tiap fase
    perubahan = []
    for key, fase in progress["fase"].items():
        status_lama = fase.get("status", False)
        status_baru = check_fase_status(fase)

        if status_baru and not status_lama:
            fase["tanggal_selesai"] = datetime.now().isoformat()
            perubahan.append(f"✅ Fase '{key}' ({fase['nama']}) SELESAI")

        fase["status"] = status_baru

    save_progress(progress)
    return progress, perubahan


def hitung_stat(progress):
    """Hitung statistik progress."""
    fase_list = progress.get("fase", {})
    total = len(fase_list)
    selesai = sum(1 for f in fase_list.values() if f.get("status", False))
    belum = total - selesai
    persen = (selesai / total * 100) if total > 0 else 0

    sisa_hari = sum(
        f.get("estimasi_hari", 0)
        for f in fase_list.values()
        if not f.get("status", False)
    )

    return {
        "total": total,
        "selesai": selesai,
        "belum": belum,
        "persen": round(persen, 1),
        "sisa_hari": sisa_hari,
    }


def get_next_step(progress):
    """Cari fase berikutnya yang belum selesai."""
    for key, fase in progress.get("fase", {}).items():
        if not fase.get("status", False):
            return key, fase
    return None, None


# ============================================================
# RENDER
# ============================================================
def progress_bar(persen, length=30):
    """Bikin progress bar ASCII."""
    filled = int(length * persen / 100)
    return "█" * filled + "░" * (length - filled)


def print_report(progress, stat, next_key, next_fase, verbose=False):
    """Print laporan ke terminal."""
    print()
    print("=" * 65)
    print(f"📊 PROGRESS: {progress.get('project', 'Pustaka Struk')} v{progress.get('version', '2.0')}")
    print("=" * 65)
    print(f"✅ Selesai   : {stat['selesai']}/{stat['total']} fase")
    print(f"⬜ Belum     : {stat['belum']} fase")
    print(f"📈 Progress  : {stat['persen']}%")
    print(f"⏱️  Sisa kerja : ~{stat['sisa_hari']} hari")
    print("=" * 65)
    print(f"[{progress_bar(stat['persen'])}] {stat['persen']}%")
    print("=" * 65)
    print()

    if verbose:
        print("📋 DETAIL PER FASE:")
        print("-" * 65)
        for key, fase in progress.get("fase", {}).items():
            icon = "✅" if fase.get("status") else "⬜"
            print(f"{icon} {key}: {fase['nama']} ({fase['estimasi_hari']} hari)")
            if not fase.get("status"):
                for detail in get_file_details(fase):
                    print(f"     {detail['icon']} {detail['file']}")
        print("-" * 65)
        print()

    # Next step
    if next_fase:
        print("🎯 NEXT STEP:")
        print("-" * 65)
        print(f"   Fase   : {next_key}")
        print(f"   Nama   : {next_fase['nama']}")
        print(f"   Desc   : {next_fase['deskripsi']}")
        print(f"   Estim  : {next_fase['estimasi_hari']} hari")
        print(f"   File   :")
        for detail in get_file_details(next_fase):
            print(f"     {detail['icon']} {detail['file']}")
        print("-" * 65)
    else:
        print("🎉 SEMUA FASE SELESAI! Proyek rampung!")

    print("=" * 65)
    print()


def write_markdown_report(progress, stat, next_key, next_fase):
    """Tulis laporan ke PROGRESS_REPORT.md."""
    lines = []
    lines.append("# 📊 Progress Report\n\n")
    lines.append(f"**Update:** {datetime.now().strftime('%d %B %Y, %H:%M')}\n\n")
    lines.append(f"## Status: {stat['persen']}% ({stat['selesai']}/{stat['total']} fase)\n\n")
    lines.append(f"```\n[{progress_bar(stat['persen'])}] {stat['persen']}%\n```\n\n")
    lines.append(f"- ✅ Selesai: {stat['selesai']}\n")
    lines.append(f"- ⬜ Belum: {stat['belum']}\n")
    lines.append(f"- ⏱️ Sisa kerja: ~{stat['sisa_hari']} hari\n\n")
    lines.append("## Detail Fase\n\n")

    for key, fase in progress.get("fase", {}).items():
        icon = "✅" if fase.get("status") else "⬜"
        lines.append(f"### {icon} {fase['nama']}\n\n")
        lines.append(f"- **ID:** `{key}`\n")
        lines.append(f"- **Deskripsi:** {fase['deskripsi']}\n")
        lines.append(f"- **Estimasi:** {fase['estimasi_hari']} hari\n")

        if fase.get("tanggal_selesai"):
            lines.append(f"- **Selesai:** {fase['tanggal_selesai'][:10]}\n")

        lines.append(f"\n**File penanda:**\n")
        for detail in get_file_details(fase):
            lines.append(f"- {detail['icon']} `{detail['file']}`\n")
        lines.append("\n")

    if next_fase:
        lines.append(f"## 🎯 Next Step\n\n")
        lines.append(f"**{next_fase['nama']}** — {next_fase['deskripsi']}\n\n")
        lines.append(f"Estimasi: {next_fase['estimasi_hari']} hari\n")

    Path(REPORT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)


def print_json(progress, stat, next_key, next_fase):
    """Print output JSON."""
    output = {
        "project": progress.get("project"),
        "version": progress.get("version"),
        "last_update": progress.get("last_update"),
        "stat": stat,
        "next_step": {
            "id": next_key,
            "nama": next_fase["nama"] if next_fase else None,
            "deskripsi": next_fase["deskripsi"] if next_fase else None,
        } if next_fase else None,
        "fase": progress.get("fase"),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Auto-scan progress proyek Pustaka Struk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--report", action="store_true", help="Tampilkan detail lengkap")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    print("🔍 Scanning progress...")
    progress, perubahan = scan_and_update()
    stat = hitung_stat(progress)
    next_key, next_fase = get_next_step(progress)

    if args.json:
        print_json(progress, stat, next_key, next_fase)
        return

    if perubahan:
        print()
        for p in perubahan:
            print(p)
        print()

    print_report(progress, stat, next_key, next_fase, verbose=args.report)

    # Tulis markdown report
    write_markdown_report(progress, stat, next_key, next_fase)
    print(f"💾 Report tersimpan: {REPORT_FILE}")
    print(f"💾 Progress tersimpan: {PROGRESS_FILE}")
    print()


if __name__ == "__main__":
    main()
