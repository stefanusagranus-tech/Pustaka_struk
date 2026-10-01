"""
utils/plu_loader.py
Helper untuk load & manage file CSV PLU per periode.
"""
import os
import re
import pandas as pd
from datetime import date, datetime
from pathlib import Path


# ============================================================
# KONFIGURASI
# ============================================================
DATA_DIR = "data/plu_psm"


# ============================================================
# PARSE NAMA FILE
# ============================================================
def parse_filename(filename):
    """
    Parse nama file: '2026-10-01_15.csv' → dict info.
    
    Format: YYYY-MM-DD_DD.csv
    Contoh: 2026-10-01_15.csv artinya:
        - Tahun 2026
        - Bulan 10
        - Tanggal mulai 01
        - Tanggal akhir 15
    """
    # Hapus ekstensi
    name = filename.replace(".csv", "")

    # Regex: 2026-10-01_15
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
        "periode_label": f"{tgl_awal}-{tgl_akhir} {datetime(int(tahun), int(bulan), 1).strftime('%b %Y')}",
    }


# ============================================================
# LIST FILE
# ============================================================
def list_plu_files():
    """List semua file CSV PLU di folder data/plu_psm/."""
    if not os.path.exists(DATA_DIR):
        return []

    files = []
    for f in os.listdir(DATA_DIR):
        if f.endswith(".csv"):
            info = parse_filename(f)
            if info:
                info["path"] = os.path.join(DATA_DIR, f)
                files.append(info)

    # Sort by tahun, bulan, tgl_awal
    files.sort(key=lambda x: (x["tahun"], x["bulan"], x["tgl_awal"]))
    return files


# ============================================================
# FIND FILE BY DATE
# ============================================================
def find_file_by_date(tgl):
    """
    Cari file PLU yang cocok dengan tanggal.
    
    Args:
        tgl: datetime.date object
    
    Returns:
        dict info file, atau None kalau gak ada.
    """
    files = list_plu_files()

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
    Baca file CSV PLU. Return list of dict {plu, nama, mekanisme, brand}.
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

        # Ambil info tambahan kalau ada
        nama = ""
        mekanisme = ""
        brand = ""

        for col in df.columns:
            col_lower = col.strip().lower()
            if col_lower in ["desc", "description", "nama"]:
                nama = str(row[col]) if pd.notna(row[col]) else ""
            elif col_lower in ["mekanisme", "mekanisme"]:
                mekanisme = str(row[col]) if pd.notna(row[col]) else ""
            elif col_lower in ["brand", "merek"]:
                brand = str(row[col]) if pd.notna(row[col]) else ""

        result.append({
            "plu": plu_val,
            "nama": nama,
            "mekanisme": mekanisme,
            "brand": brand,
        })

    return result


def load_plu_by_date(tgl):
    """Load PLU untuk tanggal tertentu."""
    file_info = find_file_by_date(tgl)

    if file_info is None:
        return [], None

    plu_list = load_plu_from_file(file_info["path"])
    return plu_list, file_info


# ============================================================
# SAVE FILE
# ============================================================
def save_plu_csv(uploaded_file, tahun, bulan, tgl_awal, tgl_akhir):
    """
    Simpan file CSV yang diupload.
    Return: (success, message, filepath)
    """
    # Bikin folder
    os.makedirs(DATA_DIR, exist_ok=True)

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
    filepath = os.path.join(DATA_DIR, filename)

    # Simpan
    df.to_csv(filepath, index=False)

    return True, f"File disimpan: {filename} ({len(df)} PLU)", filepath


def delete_plu_file(filename):
    """Hapus file PLU."""
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False
