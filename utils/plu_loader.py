"""
utils/plu_loader.py
Helper untuk load & manage file PLU per kategori & periode.
Support: CSV, Excel (.xlsx/.xls), PDF.
"""
import os
import re
import io
import pandas as pd
from datetime import date, datetime
from pathlib import Path


# ============================================================
# KONFIGURASI
# ============================================================
DATA_DIR = "data/plu"

KATEGORI = {
    "psm": {"nama": "PSM", "icon": "📊", "desc": "PLU harga spesial"},
    "sg": {"nama": "Serba Gratis (SG)", "icon": "🎁", "desc": "PLU beli X gratis Y"},
    "pwp": {"nama": "PWP", "icon": "🛒", "desc": "Promo What Purchase"},
    "suger": {"nama": "Suger", "icon": "🍬", "desc": "PLU kategori suger"},
}

# Format yang didukung
SUPPORTED_EXTENSIONS = ["csv", "xlsx", "xls", "pdf"]


def get_kategori_dir(kategori):
    return os.path.join(DATA_DIR, kategori)


# ============================================================
# HELPER: BACA CSV
# ============================================================
def _safe_read_csv(filepath_or_buffer):
    """Baca CSV dengan berbagai fallback."""
    for kwargs in [
        {},
        {"on_bad_lines": "skip"},
        {"engine": "python", "on_bad_lines": "skip"},
        {"sep": None, "engine": "python", "on_bad_lines": "skip"},
    ]:
        try:
            if hasattr(filepath_or_buffer, "seek"):
                filepath_or_buffer.seek(0)
            return pd.read_csv(filepath_or_buffer, **kwargs)
        except Exception:
            continue
    raise Exception("Semua cara baca CSV gagal")


# ============================================================
# HELPER: BACA EXCEL
# ============================================================
def _safe_read_excel(filepath_or_buffer):
    """Baca Excel file."""
    try:
        if hasattr(filepath_or_buffer, "seek"):
            filepath_or_buffer.seek(0)
        return pd.read_excel(filepath_or_buffer)
    except Exception as e:
        raise Exception(f"Gagal baca Excel: {e}")


# ============================================================
# HELPER: BACA PDF
# ============================================================
def _read_pdf_tables(filepath_or_buffer):
    """
    Baca tabel dari PDF pakai pdfplumber.
    Return list of DataFrame (1 per halaman).
    """
    try:
        import pdfplumber
    except ImportError:
        raise Exception("Library pdfplumber belum terinstall. "
                        "Tambah 'pdfplumber' di requirements.txt")

    dfs = []

    try:
        with pdfplumber.open(filepath_or_buffer) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Coba extract tables
                tables = page.extract_tables()

                if not tables:
                    # Fallback: extract text jadi 1 kolom
                    text = page.extract_text()
                    if text:
                        lines = text.split("\n")
                        dfs.append(pd.DataFrame({"text": lines}))
                    continue

                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # Baris pertama = header
                    header = table[0]
                    rows = table[1:]

                    # Bersihkan header
                    header = [
                        str(h).strip() if h else f"col_{i}"
                        for i, h in enumerate(header)
                    ]

                    df = pd.DataFrame(rows, columns=header)
                    dfs.append(df)
    except Exception as e:
        raise Exception(f"Gagal baca PDF: {e}")

    return dfs


def _pdf_to_dataframe(filepath_or_buffer, target_plu=True):
    """
    Baca PDF → gabungkan semua tabel → cari kolom PLU.
    Return DataFrame.
    """
    dfs = _read_pdf_tables(filepath_or_buffer)

    if not dfs:
        raise Exception("PDF tidak punya tabel yang bisa dibaca.")

    # Cari DataFrame yang punya kolom PLU
    for df in dfs:
        # Cek kolom header
        for col in df.columns:
            col_lower = str(col).strip().lower()
            if "plu" in col_lower:
                return df

    # Kalau gak ada kolom PLU di header, coba pakai tabel pertama
    # dan cari kolom yang isinya angka semua (kandidat PLU)
    main_df = dfs[0]

    return main_df


# ============================================================
# HELPER: DETEKSI FORMAT
# ============================================================
def _detect_and_read(filepath_or_buffer, filename=""):
    """
    Auto-detect format dari nama file / isi.
    Return DataFrame.
    """
    filename_lower = str(filename).lower()

    # Deteksi dari ekstensi
    if filename_lower.endswith(".csv"):
        return _safe_read_csv(filepath_or_buffer), "csv"

    if filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
        return _safe_read_excel(filepath_or_buffer), "excel"

    if filename_lower.endswith(".pdf"):
        return _pdf_to_dataframe(filepath_or_buffer), "pdf"

    # Fallback: coba CSV dulu, baru Excel
    try:
        return _safe_read_csv(filepath_or_buffer), "csv"
    except Exception:
        pass

    try:
        return _safe_read_excel(filepath_or_buffer), "excel"
    except Exception:
        pass

    raise Exception(
        "Format file tidak dikenali. Gunakan CSV, Excel, atau PDF."
    )


# ============================================================
# PARSE NAMA FILE
# ============================================================
def parse_filename(filename):
    name = re.sub(r"\.(csv|xlsx|xls|pdf)$", "", filename, flags=re.IGNORECASE)
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
# LIST FILE
# ============================================================
def list_plu_files(kategori):
    folder = get_kategori_dir(kategori)
    if not os.path.exists(folder):
        return []

    files = []
    for f in os.listdir(folder):
        ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
        if ext in SUPPORTED_EXTENSIONS:
            info = parse_filename(f)
            if info:
                info["path"] = os.path.join(folder, f)
                info["kategori"] = kategori
                info["format"] = ext
                files.append(info)

    files.sort(key=lambda x: (x["tahun"], x["bulan"], x["tgl_awal"]))
    return files


def list_all_files():
    result = {}
    for kat in KATEGORI.keys():
        result[kat] = list_plu_files(kat)
    return result


# ============================================================
# FIND FILE BY DATE
# ============================================================
def find_file_by_date(kategori, tgl):
    files = list_plu_files(kategori)
    for f in files:
        if (f["tahun"] == tgl.year
                and f["bulan"] == tgl.month
                and f["tgl_awal"] <= tgl.day <= f["tgl_akhir"]):
            return f
    return None


# ============================================================
# LOAD PLU
# ============================================================
def _extract_plu_from_df(df):
    """Ekstrak PLU dari DataFrame. Return list of dict."""
    if df.empty:
        return []

    # Cari kolom PLU (case-insensitive, partial match)
    plu_col = None
    for col in df.columns:
        col_lower = str(col).strip().lower()
        if col_lower == "plu":
            plu_col = col
            break

    # Kalau gak ada exact "plu", coba kolom yang mengandung "plu"
    if plu_col is None:
        for col in df.columns:
            if "plu" in str(col).strip().lower():
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

        info = {"plu": plu_val}

        for col in df.columns:
            col_lower = str(col).strip().lower()
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


def load_plu_from_file(filepath):
    """Load PLU dari file (auto-detect format)."""
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "rb") as f:
            df, fmt = _detect_and_read(f, filename=filepath)
    except Exception as e:
        print(f"Error baca {filepath}: {e}")
        return []

    return _extract_plu_from_df(df)


def load_plu_by_date(kategori, tgl):
    file_info = find_file_by_date(kategori, tgl)
    if file_info is None:
        return [], None
    plu_list = load_plu_from_file(file_info["path"])
    return plu_list, file_info


# ============================================================
# SAVE
# ============================================================
def save_plu_csv(uploaded_file, kategori, tahun, bulan, tgl_awal, tgl_akhir):
    """
    Simpan file PLU yang diupload.
    Support: CSV, Excel, PDF.
    File akan disimpan dalam format CSV agar ringan.
    """
    folder = get_kategori_dir(kategori)
    os.makedirs(folder, exist_ok=True)

    # Baca file apapun formatnya
    try:
        df, fmt = _detect_and_read(uploaded_file, filename=uploaded_file.name)
    except Exception as e:
        return False, f"Gagal baca file: {e}", None

    if df.empty:
        return False, "File kosong atau tidak ada data.", None

    # Cek kolom PLU
    plu_col = None
    for col in df.columns:
        if str(col).strip().lower() == "plu":
            plu_col = col
            break

    if plu_col is None:
        for col in df.columns:
            if "plu" in str(col).strip().lower():
                plu_col = col
                break

    if plu_col is None:
        return False, (
            "Kolom 'PLU' tidak ditemukan. "
            f"Kolom yang ada: {', '.join(str(c) for c in df.columns)}"
        ), None

    # Bersihkan: buang baris yang PLU kosong
    df = df[df[plu_col].notna()].copy()

    # Nama file (selalu simpan sebagai CSV)
    filename = f"{tahun}-{bulan:02d}-{tgl_awal:02d}_{tgl_akhir:02d}.csv"
    filepath = os.path.join(folder, filename)

    # Simpan sebagai CSV
    df.to_csv(filepath, index=False)

    return True, (
        f"File disimpan: {filename} "
        f"({len(df)} PLU, dari format {fmt.upper()})"
    ), filepath


def delete_plu_file(kategori, filename):
    filepath = os.path.join(get_kategori_dir(kategori), filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


# ============================================================
# STATISTIK
# ============================================================
def get_stats():
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
