"""
utils/plu_loader.py
Helper untuk load & manage file CSV PLU per kategori & periode.
Kategori: psm, sg, pwp, suger
"""
import os
import re
import pandas as pd
from datetime import date, datetime
from pathlib import Path


# ============================================================
# KONFIGURASI
# ============================================================
DATA_DIR = "data/plu"

# Kategori yang didukung
KATEGORI = {
    "psm": {
        "nama": "PSM",
        "icon": "📊",
        "desc": "PLU harga spesial",
    },
    "sg": {
        "nama": "Serba Gratis (SG)",
        "icon": "🎁",
        "desc": "PLU beli X gratis Y",
    },
    "pwp": {
        "nama": "PWP",
        "icon": "🛒",
        "desc": "Promo What Purchase",
    },
    "suger": {
        "nama": "Suger",
        "icon": "🍬",
        "desc": "PLU kategori suger",
    },
}


def get_kategori_dir(kategori):
    """Path folder untuk kategori tertentu."""
    return os.path.join(DATA_DIR, kategori)


# ============================================================
# PARSE NAMA FILE
# ============================================================
def parse_filename(filename):
    """
    Parse nama file: '2026-10-01_15.csv' → dict info.
    Format: YYYY-MM-DD_DD.csv
    """
    name = filename.replace(".csv", "")
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})_(\d{2})", name)
    if not match:
        return None

    tahun, bulan, tgl_awal, tgl_akhir = match.groups()

    return {
        "filename": filename,
        "tahun": int(tahun),
        "bulan": int(bulan),
        "tgl_awal": int(tgl_awal),
        "tgl_akhir": int(tgl_akhir),
        "periode_label": (
            f"{tgl_awal}-{tgl_akhir} "
            f"{datetime(int(tahun), int(bulan), 1).strftime('%b %Y')}"
        ),
    }


# ============================================================
# LIST FILE PER KATEGORI
# ============================================================
def list_plu_files(kategori):
    """List semua file CSV PLU di folder kategori tertentu."""
    folder = get_kategori_dir(kategori)

    if not os.path.exists(folder):
        return []

    files = []
    for f in os.listdir(folder):
        if f.endswith(".csv"):
            info = parse_filename(f)
            if info:
                info["path"] = os.path.join(folder, f)
                info["kategori"] = kategori
                files.append(info)

    files.sort(key=lambda x: (x["tahun"], x["bulan"], x["tgl_awal"]))
    return files


def list_all_files():
    """List semua file di semua kategori."""
    result = {}
    for kat in KATEGORI.keys():
        result[kat] = list_plu_files(kat)
    return result


# ============================================================
# FIND FILE BY DATE
# ============================================================
def find_file_by_date(kategori, tgl):
    """Cari file PLU untuk kategori & tanggal tertentu."""
    files = list_plu_files(kategori)

    for f in files:
        if (f["tahun"] == tgl.year
                and f["bulan"] == tgl.month
                and f["tgl_awal"] <= tgl.day <= f["tgl_akhir"]):
            return f

    return None


# ============================================================
# LOAD PLU DARI FILE
# ============================================================
def load_plu_from_file(filepath):
    """
    Baca file CSV PLU. Return list of dict.
    Kolom wajib: PLU
    Kolom optional: Desc, Mekanisme, Brand, Kat, Qty, dll.
    """
    if not os.path.exists(filepath):
        return []

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Error baca {filepath}: {e}")
        return []

    # Cari kolom PLU (case-insensitive)
    plu_col = None
    for col in df.columns:
        if col.strip().lower() == "plu":
            plu_col = col
            break

    if plu_col is None:
        return []

    result = []
    for _, row in df.iterrows():
        try:
            plu_val = int(float(row[plu_col]))
        except (ValueError, TypeError):
            continue

        # Ambil info tambahan
        info = {"plu": plu_val}

        for col in df.columns:
            col_lower = col.strip().lower()
            if col_lower in ["desc", "description", "nama"]:
                info["nama"] = str(row[col]) if pd.notna(row[col]) else ""
            elif col_lower == "mekanisme":
                info["mekanisme"] = str(row[col]) if pd.notna(row[col]) else ""
            elif col_lower in ["brand", "merek"]:
                info["brand"] = str(row[col]) if pd.notna(row[col]) else ""
            elif col_lower == "kat":
                info["kat"] = str(row[col]) if pd.notna(row[col]) else ""
            elif col_lower in ["qty", "quantity", "syarat_qty"]:
                try:
                    info["qty"] = int(float(row[col]))
                except (ValueError, TypeError):
                    info["qty"] = None
            elif col_lower in ["beli_qty", "beli"]:
                try:
                    info["beli_qty"] = int(float(row[col]))
                except (ValueError, TypeError):
                    info["beli_qty"] = None

        result.append(info)

    return result


def load_plu_by_date(kategori, tgl):
    """Load PLU untuk kategori & tanggal tertentu."""
    file_info = find_file_by_date(kategori, tgl)

    if file_info is None:
        return [], None

    plu_list = load_plu_from_file(file_info["path"])
    return plu_list, file_info


# ============================================================
# SAVE FILE
# ============================================================
def save_plu_csv(uploaded_file, kategori, tahun, bulan, tgl_awal, tgl_akhir):
    """Simpan file CSV yang diupload ke kategori tertentu."""
    folder = get_kategori_dir(kategori)
    os.makedirs(folder, exist_ok=True)

    # Validasi
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        return False, f"Gagal baca CSV: {e}", None

    # Cek kolom PLU
    plu_col = None
    for col in df.columns:
        if col.strip().lower() == "plu":
            plu_col = col
            break

    if plu_col is None:
        return False, "Kolom 'PLU' tidak ditemukan di CSV.", None

    # Nama file
    filename = f"{tahun}-{bulan:02d}-{tgl_awal:02d}_{tgl_akhir:02d}.csv"
    filepath = os.path.join(folder, filename)

    # Simpan
    df.to_csv(filepath, index=False)

    return True, f"File disimpan: {filename} ({len(df)} PLU)", filepath


def delete_plu_file(kategori, filename):
    """Hapus file PLU."""
    filepath = os.path.join(get_kategori_dir(kategori), filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


# ============================================================
# STATISTIK
# ============================================================
def get_stats():
    """Statistik file per kategori."""
    stats = {}
    for kat, info in KATEGORI.items():
        files = list_plu_files(kat)
        total_plu = sum(len(load_plu_from_file(f["path"])) for f in files)
        stats[kat] = {
            "nama": info["nama"],
            "icon": info["icon"],
            "jumlah_file": len(files),
            "total_plu": total_plu,
        }
    return stats
