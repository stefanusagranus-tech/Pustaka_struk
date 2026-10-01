"""
utils/plu_loader.py
Helper untuk load & manage file PLU per kategori & periode.
Support: CSV, Excel (.xlsx/.xls), PDF.
Fitur: Auto-detect delimiter, deteksi kolom fleksibel, parse mekanisme.
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

KATEGORI = {
    "psm": {"nama": "PSM", "icon": "📊", "desc": "PLU harga spesial"},
    "sg": {"nama": "Serba Gratis (SG)", "icon": "🎁", "desc": "PLU beli X gratis Y"},
    "pwp": {"nama": "PWP", "icon": "🛒", "desc": "Promo What Purchase"},
    "suger": {"nama": "Suger", "icon": "🍬", "desc": "PLU kategori suger"},
}

SUPPORTED_EXTENSIONS = ["csv", "xlsx", "xls", "pdf"]


def get_kategori_dir(kategori):
    """Path folder untuk kategori tertentu."""
    return os.path.join(DATA_DIR, kategori)


# ============================================================
# HELPER: DETEKSI KOLOM (FLEKSIBEL)
# ============================================================
def find_column(df, keywords):
    """
    Cari kolom di DataFrame yang namanya mengandung salah satu keyword.
    Return nama kolom pertama yang match, atau None.

    Args:
        df: DataFrame
        keywords: list of str — keyword untuk dicari (lowercase)
    """
    for col in df.columns:
        col_lower = str(col).strip().lower().replace("_", " ").replace(".", " ")
        for kw in keywords:
            if kw in col_lower:
                return col
    return None


# ============================================================
# PARSE MEKANISME
# ============================================================
def parse_mekanisme(text):
    """
    Parse teks mekanisme jadi struktur data.

    Contoh input:
        "BELI 2 GRATIS 1"
        "BELI 3 GRATIS 1"
        "BELI 1 GRATIS ELLIPS"
        "Beli 2 Gratis 1 (Min Rp 50.000)"

    Return dict:
        {
            "beli_qty": 2,
            "gratis_qty": 1,
            "gratis_item": "",
            "raw": "BELI 2 GRATIS 1",
        }
    """
    if not text or pd.isna(text):
        return {
            "beli_qty": None,
            "gratis_qty": None,
            "gratis_item": "",
            "raw": "",
        }

    text_str = str(text).strip()
    text_lower = text_str.lower()

    # Pattern 1: "beli X gratis Y" (angka)
    pattern = r"beli\s+(\d+)\s+gratis\s+(\d+)"
    match = re.search(pattern, text_lower)

    if match:
        return {
            "beli_qty": int(match.group(1)),
            "gratis_qty": int(match.group(2)),
            "gratis_item": "",
            "raw": text_str,
        }

    # Pattern 2: "beli X gratis <NAMA ITEM>"
    pattern_item = r"beli\s+(\d+)\s+gratis\s+([a-zA-Z\s]+?)(?:\s*\(|$)"
    match_item = re.search(pattern_item, text_lower)

    if match_item:
        return {
            "beli_qty": int(match_item.group(1)),
            "gratis_qty": 1,
            "gratis_item": match_item.group(2).strip().upper(),
            "raw": text_str,
        }

    # Fallback: ambil angka pertama sebagai beli_qty
    match_num = re.search(r"\d+", text_lower)
    if match_num:
        return {
            "beli_qty": int(match_num.group()),
            "gratis_qty": 1,
            "gratis_item": "",
            "raw": text_str,
        }

    return {
        "beli_qty": None,
        "gratis_qty": None,
        "gratis_item": "",
        "raw": text_str,
    }


# ============================================================
# HELPER: BACA CSV
# ============================================================
def _safe_read_csv(filepath_or_buffer):
    """Baca CSV dengan berbagai fallback + auto-detect delimiter."""
    for kwargs in [
        {"sep": None, "engine": "python", "on_bad_lines": "skip"},
        {},
        {"on_bad_lines": "skip"},
        {"engine": "python", "on_bad_lines": "skip"},
        {"sep": "\t", "engine": "python", "on_bad_lines": "skip"},
        {"sep": ";", "engine": "python", "on_bad_lines": "skip"},
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
    """Baca tabel dari PDF. Support format tabel & format teks bebas."""
    try:
        import pdfplumber
    except ImportError:
        raise Exception(
            "Library pdfplumber belum terinstall. "
            "Tambah 'pdfplumber' di requirements.txt"
        )

    dfs = []

    try:
        with pdfplumber.open(filepath_or_buffer) as pdf:
            for page in pdf.pages:
                # === CARA 1: Tabel rapi ===
                tables = page.extract_tables()

                if tables:
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        header = [
                            str(h).strip() if h else f"col_{i}"
                            for i, h in enumerate(table[0])
                        ]
                        df = pd.DataFrame(table[1:], columns=header)
                        dfs.append(df)
                    continue

                # === CARA 2: Text bebas pakai regex ===
                text = page.extract_text()
                if not text:
                    continue

                pattern = r"(\d{5,6})\s+(.+?)(?=\s+\d{5,6}\s+|$)"
                matches = re.findall(pattern, text, re.DOTALL)

                if matches:
                    rows = []
                    for plu, desc in matches:
                        desc_clean = " ".join(desc.split())
                        rows.append({
                            "PLU": int(plu),
                            "Descp": desc_clean,
                        })
                    if rows:
                        dfs.append(pd.DataFrame(rows))

    except Exception as e:
        raise Exception(f"Gagal baca PDF: {e}")

    return dfs


def _pdf_to_dataframe(filepath_or_buffer):
    """Baca PDF → gabungkan semua tabel → cari kolom PLU."""
    dfs = _read_pdf_tables(filepath_or_buffer)

    if not dfs:
        raise Exception("PDF tidak punya tabel yang bisa dibaca.")

    for df in dfs:
        for col in df.columns:
            if "plu" in str(col).strip().lower():
                return df

    return dfs[0]


# ============================================================
# HELPER: DETEKSI FORMAT
# ============================================================
def _detect_and_read(filepath_or_buffer, filename=""):
    """Auto-detect format dari nama file / isi."""
    filename_lower = str(filename).lower()

    if filename_lower.endswith(".csv"):
        return _safe_read_csv(filepath_or_buffer), "csv"

    if filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
        return _safe_read_excel(filepath_or_buffer), "excel"

    if filename_lower.endswith(".pdf"):
        return _pdf_to_dataframe(filepath_or_buffer), "pdf"

    # Fallback
    try:
        return _safe_read_csv(filepath_or_buffer), "csv"
    except Exception:
        pass

    try:
        return _safe_read_excel(filepath_or_buffer), "excel"
    except Exception:
        pass

    raise Exception("Format file tidak dikenali. Gunakan CSV, Excel, atau PDF.")

# ⬇️⬇️⬇️ LANJUT KE BAGIAN 2 ⬇️⬇️⬇️

# ============================================================
# PARSE NAMA FILE
# ============================================================
def parse_filename(filename):
    """Parse nama file: '2026-10-01_07.csv' → dict info."""
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
    """List semua file CSV/Excel/PDF PLU di folder kategori tertentu."""
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
# LOAD PLU — EKSTRAKSI FLEKSIBEL
# ============================================================
def _extract_plu_from_df(df):
    """
    Ekstrak PLU + info dari DataFrame.
    Deteksi kolom pakai keyword — fleksibel.
    """
    if df.empty:
        return []

    # === DETEKSI KOLOM PLU ===
    plu_col = find_column(df, ["plu"])
    if plu_col is None:
        return []

    # === DETEKSI KOLOM LAIN (fleksibel) ===
    nama_col = find_column(df, [
        "descp", "desc", "description", "nama", "barang", "produk", "item"
    ])
    mekanisme_col = find_column(df, [
        "mekanisme", "mekanisme promo", "promo mekanisme"
    ])
    brand_col = find_column(df, ["brand", "merek", "merk"])
    kat_col = find_column(df, ["kat", "kategori"])
    qty_col = find_column(df, ["syarat qty", "qty", "quantity"])
    beli_col = find_column(df, ["beli qty", "beli"])

    result = []
    for _, row in df.iterrows():
        # Skip baris kosong
        try:
            plu_val = int(float(row[plu_col]))
        except (ValueError, TypeError):
            continue

        info = {"plu": plu_val}

        # Ambil deskripsi
        if nama_col and pd.notna(row[nama_col]):
            info["nama"] = str(row[nama_col]).strip()
        else:
            info["nama"] = ""

        # Ambil mekanisme + parse
        if mekanisme_col and pd.notna(row[mekanisme_col]):
            mek_text = str(row[mekanisme_col]).strip()
            info["mekanisme"] = mek_text

            parsed = parse_mekanisme(mek_text)
            info["beli_qty"] = parsed["beli_qty"]
            info["gratis_qty"] = parsed["gratis_qty"]
            info["gratis_item"] = parsed["gratis_item"]
        else:
            info["mekanisme"] = ""
            info["beli_qty"] = None
            info["gratis_qty"] = None
            info["gratis_item"] = ""

        # Ambil brand
        if brand_col and pd.notna(row[brand_col]):
            info["brand"] = str(row[brand_col]).strip()
        else:
            info["brand"] = ""

        # Ambil kategori
        if kat_col and pd.notna(row[kat_col]):
            info["kat"] = str(row[kat_col]).strip()
        else:
            info["kat"] = ""

        # Ambil qty (kalau ada kolom qty eksplisit)
        if qty_col and pd.notna(row[qty_col]):
            try:
                info["qty"] = int(float(row[qty_col]))
            except (ValueError, TypeError):
                info["qty"] = None
        else:
            # Fallback: pakai syarat dari mekanisme (beli + gratis)
            if info.get("beli_qty") and info.get("gratis_qty"):
                info["qty"] = info["beli_qty"] + info["gratis_qty"]
            else:
                info["qty"] = None

        # Ambil beli_qty (kalau ada kolom eksplisit)
        if beli_col and pd.notna(row[beli_col]):
            try:
                info["beli_qty"] = int(float(row[beli_col]))
            except (ValueError, TypeError):
                pass

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
    """Load PLU untuk kategori & tanggal tertentu."""
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
    Simpan file PLU yang diupload (CSV/Excel/PDF) sebagai CSV.
    """
    folder = get_kategori_dir(kategori)
    os.makedirs(folder, exist_ok=True)

    # Baca file
    try:
        df, fmt = _detect_and_read(uploaded_file, filename=uploaded_file.name)
    except Exception as e:
        return False, f"Gagal baca file: {e}", None

    if df.empty:
        return False, "File kosong atau tidak ada data.", None

    # Cek kolom PLU
    plu_col = find_column(df, ["plu"])

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
