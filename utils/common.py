import sqlite3
import os
import shutil
import zipfile
import json          ← tambahkan di sini
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import html
import re

from utils.plu_dict import PLU_NAMES, get_nama_plu, get_plu_normalized

STRUK_WIDTH = 42


# ============================================================
# AUTO-NORMALISASI PLU
# ============================================================
def normalize_plu_series(series, mode="asli"):
    """
    Normalisasi PLU dari database ke format asli.
    mode: asli | buang_1 | buang_2 | div_10 | div_100
    """
    s = pd.to_numeric(series, errors="coerce")
    if mode == "asli":
        return s
    if mode == "buang_1":
        return pd.to_numeric(
            s.astype(str).str.replace(r"\.0$", "", regex=True).str[:-1],
            errors="coerce"
        )
    if mode == "buang_2":
        return pd.to_numeric(
            s.astype(str).str.replace(r"\.0$", "", regex=True).str[:-2],
            errors="coerce"
        )
    if mode == "div_10":
        return s / 10
    if mode == "div_100":
        return s / 100
    return s


def detect_best_plu_mode(df_detail, plu_target_set):
    """
    Coba beberapa mode normalisasi PLU, pilih yang paling banyak match.
    Return: (mode, jumlah_match, df_hasil_dengan_kolom_plu_norm)
    """
    modes = ["asli", "buang_1", "buang_2", "div_10", "div_100"]
    best_mode = "asli"
    best_count = 0
    best_df = pd.DataFrame()

    for mode in modes:
        df_temp = df_detail.copy()
        df_temp["plu_norm"] = normalize_plu_series(df_temp["plu"], mode)
        df_temp["plu_norm_int"] = df_temp["plu_norm"].round().astype("Int64")

        mask = df_temp["plu_norm_int"].isin(plu_target_set)
        count = int(mask.sum())

        if count > best_count:
            best_count = count
            best_mode = mode
            best_df = df_temp[mask].copy()

    return best_mode, best_count, best_df


# ============================================================
# BACA DATABASE
# ============================================================
def get_table_names(conn):
    q = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    return pd.read_sql(q, conn)["name"].tolist()


def load_tables(db_path, table_names):
    conn = sqlite3.connect(db_path)
    tables = get_table_names(conn)
    dfs = {}
    for tbl in table_names:
        if tbl in tables:
            try:
                dfs[tbl] = pd.read_sql("SELECT * FROM `" + tbl + "`", conn)
            except Exception as e:
                st.warning("Gagal baca tabel " + tbl + ": " + str(e))
                dfs[tbl] = pd.DataFrame()
        else:
            dfs[tbl] = pd.DataFrame()
    conn.close()
    return dfs


def extract_zip_and_find_db(uploaded_zip, extract_path):
    """Extract ZIP, cari file .db, return path."""
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    os.makedirs(extract_path, exist_ok=True)
    with zipfile.ZipFile(uploaded_zip, "r") as z:
        z.extractall(extract_path)
    for root, _, files in os.walk(extract_path):
        for f in files:
            if f.endswith((".db", ".sqlite", ".sqlite3")):
                return os.path.join(root, f)
    return None


# ============================================================
# FORMAT STRUK
# ============================================================
def format_struk(raw_text, width=STRUK_WIDTH):
    if not raw_text:
        return ""
    text = raw_text.replace("|", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    result = []

    for line in lines:
        line = line.rstrip()
        stripped = line.strip()
        if re.fullmatch(r"[=\-]{5,}", stripped):
            if "=" in stripped:
                result.append("=" * width)
            else:
                result.append("-" * width)
            continue
        if stripped == "":
            result.append("")
            continue
        if len(line) > width:
            m = re.match(
                r"^(.*?)\s{2,}(\d+)\s+([\d.,]+)\s+([\d.,]+)\s*$", line
            )
            if m:
                nama, qty, harga, total = m.groups()
                kanan = f"{qty:>3} {harga:>8} {total:>9}"
                nama_max = width - len(kanan) - 1
                nama = nama[:nama_max]
                result.append(f"{nama:<{nama_max}} {kanan}")
            else:
                while len(line) > width:
                    result.append(line[:width])
                    line = line[width:]
                if line:
                    result.append(line)
        else:
            result.append(line)

    cleaned = []
    prev_empty = False
    for line in result:
        if line.strip() == "":
            if not prev_empty:
                cleaned.append("")
            prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False

    final = []
    skip_next_empty = False
    for i, line in enumerate(cleaned):
        if skip_next_empty and line.strip() == "":
            skip_next_empty = False
            continue
        skip_next_empty = False
        if re.fullmatch(r"=+", line.strip()):
            final.append(line)
            skip_next_empty = True
            continue
        final.append(line)

    return "\n".join(final)


def render_struk_html(text, width=STRUK_WIDTH):
    escaped = html.escape(text)
    char_width_px = 7.8
    container_width_px = int(width * char_width_px) + 40

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{ margin:0; padding:0; background:transparent;
                font-family:'Courier New', monospace; }}
        .struk-outer {{ display:flex; justify-content:center; padding:8px 0; }}
        .struk-container {{
            background-color:#ffffff; color:#000000;
            padding:18px 22px; border-radius:6px;
            border:1px solid #dddddd;
            box-shadow:0px 4px 12px rgba(0,0,0,0.15);
            width:{container_width_px}px; max-width:100%;
            overflow-x:auto;
        }}
        .struk-container pre {{
            margin:0; font-family:'Courier New', monospace;
            font-size:13px; line-height:1.15;
            white-space:pre;
            color:#000000; background:transparent;
        }}
    </style>
    </head>
    <body>
        <div class="struk-outer">
            <div class="struk-container"><pre>{escaped}</pre></div>
        </div>
    </body>
    </html>
    """


def generate_pdf(text):
    from fpdf import FPDF
    pdf = FPDF(unit="mm", format=(80, 297))
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=3)
    pdf.set_margins(left=3, top=3, right=3)
    pdf.set_font("Courier", size=8)
    for line in text.split("\n"):
        safe_line = line.encode("latin-1", "replace").decode("latin-1")
        pdf.cell(0, 3.0, safe_line, ln=1)
    return bytes(pdf.output())


def render_print_button(receipt_text):
    escaped = html.escape(receipt_text)
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin:0; padding:0; background:transparent; }}
        .print-btn {{
            background-color:#0066cc; color:white; border:none;
            padding:8px 16px; border-radius:6px;
            font-size:14px; cursor:pointer; font-family:sans-serif;
        }}
        .print-btn:hover {{ background-color:#0055aa; }}
    </style>
    </head>
    <body>
        <button class="print-btn" onclick="printStruk()">🖨️ Cetak / Print</button>
        <div id="print-area" style="display:none;">
            <pre style="font-family:'Courier New',monospace;font-size:10px;line-height:1.2;white-space:pre;">{escaped}</pre>
        </div>
        <script>
            function printStruk() {{
                var w = window.open('', '', 'width=400,height=600');
                w.document.write('<html><head><title>Cetak Struk</title>');
                w.document.write('<style>body{{font-family:Courier New,monospace;font-size:11px;white-space:pre;}}@page{{size:80mm auto;margin:0;}}</style>');
                w.document.write('</head><body>');
                w.document.write(document.getElementById('print-area').innerHTML);
                w.document.write('</body></html>');
                w.document.close();
                w.focus();
                setTimeout(function(){{ w.print(); }}, 300);
            }}
        </script>
    </body>
    </html>
    """


def get_struk_text(df_receipt, bill_no):
    if df_receipt.empty or "bill_no" not in df_receipt.columns:
        return None
    cols = ["header", "body1", "body2", "body3",
            "addtl1", "addtl2", "addtl3", "footer"]
    bill_str = str(bill_no).strip()
    bill_zfill = bill_str.zfill(4)
    candidates = [bill_str, bill_zfill, bill_str.lstrip("0")]
    row = None
    for c in candidates:
        match = df_receipt[df_receipt["bill_no"].astype(str).str.strip() == c]
        if not match.empty:
            row = match.iloc[0]
            break
    if row is None:
        match = df_receipt[
            df_receipt["bill_no"].astype(str).str.strip().str.zfill(4) == bill_zfill
        ]
        if not match.empty:
            row = match.iloc[0]
    if row is None:
        return None
    parts = []
    for c in cols:
        if c in row and pd.notna(row[c]) and str(row[c]).strip():
            parts.append(str(row[c]))
    raw_text = "\n".join(parts)
    return format_struk(raw_text, width=STRUK_WIDTH), raw_text


def parse_struk_items(body1):
    if not body1 or not isinstance(body1, str):
        return []
    items = []
    text = body1.replace("|", "\n")
    lines = text.split("\n")
    skip_keywords = [
        "Bon", "Kasir", "===", "---", "Total", "Disc",
        "Tunai", "Kembalian", "PPN", "Tgl", "MEMBER",
        "STAR", "Potensi", "A-POIN", "Voucher", "EXTRA",
        "STRUK", "ALFAGIFT", "QRIS", "Card", "Jenis",
        "Nomor", "Alamat", "Penerima", "Pengirim",
    ]
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(kw in line for kw in skip_keywords):
            continue
        m = re.match(
            r"^(.+?)\s+(\d+(?:\.\d+)?)\s+([\d,]+)\s+([\d,]+)\s*$", line
        )
        if m:
            nama = m.group(1).strip()
            try:
                qty = float(m.group(2))
                harga = float(m.group(3).replace(",", ""))
                total = float(m.group(4).replace(",", ""))
                if harga > 0 and len(nama) >= 3:
                    items.append({
                        "nama": nama, "qty": qty,
                        "harga": harga, "total": total,
                    })
            except ValueError:
                continue
    return items


# ============================================================
# BUILD PLU NAME DICT
# ============================================================
def build_plu_name_dict(df_receipt=None, df_detail=None):
    """
    Return dictionary PLU -> nama.

    Prioritas:
      1. Dari PLU_NAMES (hardcode di plu_dict.py) — UTAMA
      2. Fallback ke parse struk (kalau PLU_NAMES kosong)
    """
    result = {}

    # ============================================
    # PRIORITAS 1: Dari hardcode PLU_NAMES
    # ============================================
    if PLU_NAMES:
        for plu, nama in PLU_NAMES.items():
            result[plu] = nama
        return result

    # ============================================
    # PRIORITAS 2: Fallback parse struk
    # ============================================
    if df_receipt is None or df_detail is None:
        return result

    if df_receipt.empty or df_detail.empty:
        return result

    plu_names = {}
    bill_to_body = {}

    for _, r in df_receipt.iterrows():
        bill = str(r["bill_no"]).strip().zfill(4)
        bill_to_body[bill] = str(r.get("body1", ""))

    df_detail = df_detail.copy()
    df_detail["_bill_z"] = df_detail["bill_no"].astype(str).str.strip().str.zfill(4)

    bill_to_items = {}
    for bill, grp in df_detail.groupby("_bill_z"):
        items = []
        for _, r in grp.iterrows():
            try:
                items.append({
                    "plu": r["plu"],
                    "qty": float(r["qty"]) if pd.notna(r["qty"]) else 0,
                    "price": float(r["price"]) if pd.notna(r["price"]) else 0,
                })
            except Exception:
                continue
        bill_to_items[bill] = items

    for bill, body in bill_to_body.items():
        struk_items = parse_struk_items(body)
        tx_items = bill_to_items.get(bill, [])
        for s in struk_items:
            for t in tx_items:
                if (abs(t["qty"] - s["qty"]) < 0.01
                        and abs(t["price"] - s["harga"]) < 1):
                    plu = t["plu"]
                    if plu not in plu_names:
                        plu_names[plu] = {}
                    plu_names[plu][s["nama"]] = plu_names[plu].get(s["nama"], 0) + 1

    result = {}
    for plu, names in plu_names.items():
        best = max(names.items(), key=lambda x: x[1])[0]
        result[plu] = best

    return result

# ============================================================
# BUILD KASIR DICT (dari log_connection)
# ============================================================
import json


def build_kasir_dict(df_connection):
    """
    Bangun dictionary {NIK: Nama} dari log_connection.
    
    Parse JSON di kolom str_request & str_response untuk dapat
    NIK dan Nama kasir.
    
    Return: {NIK: Nama}
    """
    if df_connection is None or df_connection.empty:
        return {}

    kasir_dict = {}

    # Kolom yang mungkin: user_id, str_request, str_response
    if "user_id" not in df_connection.columns:
        return {}

    for _, r in df_connection.iterrows():
        user_id = str(r.get("user_id", "")).strip()
        if not user_id or user_id in ("nan", "None", "0"):
            continue

        str_resp = str(r.get("str_response", ""))
        str_req = str(r.get("str_request", ""))

        nama = None

        # ----- Prioritas 1: dari str_response (NAMA) -----
        if str_resp and str_resp not in ("nan", "None", ""):
            try:
                resp_json = json.loads(str_resp)
                for key in ("NAMA", "nama", "NAMA_KASIR", "nama_kasir", "USER_NAME"):
                    if key in resp_json:
                        val = str(resp_json[key]).strip()
                        if val and val not in ("nan", "None", ""):
                            nama = val
                            break
            except Exception:
                pass

        # ----- Prioritas 2: dari str_request (TRX_DATA.NAMA) -----
        if nama is None and str_req and str_req not in ("nan", "None", ""):
            try:
                req_json = json.loads(str_req)
                trx_data = req_json.get("TRX_DATA", {})
                if isinstance(trx_data, dict):
                    for key in ("NAMA", "nama", "NAMA_KASIR"):
                        if key in trx_data:
                            val = str(trx_data[key]).strip()
                            if val and val not in ("nan", "None", ""):
                                nama = val
                                break
            except Exception:
                pass

        # ----- Simpan kalau dapat NIK + Nama -----
        if user_id and nama:
            if user_id not in kasir_dict:
                kasir_dict[user_id] = nama
            else:
                # Pilih nama yang lebih panjang (kemungkinan lebih lengkap)
                if len(nama) > len(str(kasir_dict[user_id])):
                    kasir_dict[user_id] = nama

    return kasir_dict
    
    # ============================================================
# BUILD KASIR DICT (dari log_connection)
# ============================================================
import json


def build_kasir_dict(df_connection):
    """
    Bangun dictionary {NIK: Nama} dari log_connection.
    Parse JSON di kolom str_request & str_response.
    """
    if df_connection is None or df_connection.empty:
        return {}

    kasir_dict = {}

    if "user_id" not in df_connection.columns:
        return {}

    for _, r in df_connection.iterrows():
        user_id = str(r.get("user_id", "")).strip()
        if not user_id or user_id in ("nan", "None", "0"):
            continue

        str_resp = str(r.get("str_response", ""))
        str_req = str(r.get("str_request", ""))

        nama = None

        # Prioritas 1: dari str_response
        if str_resp and str_resp not in ("nan", "None", ""):
            try:
                resp_json = json.loads(str_resp)
                for key in ("NAMA", "nama", "NAMA_KASIR", "nama_kasir", "USER_NAME"):
                    if key in resp_json:
                        val = str(resp_json[key]).strip()
                        if val and val not in ("nan", "None", ""):
                            nama = val
                            break
            except Exception:
                pass

        # Prioritas 2: dari str_request
        if nama is None and str_req and str_req not in ("nan", "None", ""):
            try:
                req_json = json.loads(str_req)
                trx_data = req_json.get("TRX_DATA", {})
                if isinstance(trx_data, dict):
                    for key in ("NAMA", "nama", "NAMA_KASIR"):
                        if key in trx_data:
                            val = str(trx_data[key]).strip()
                            if val and val not in ("nan", "None", ""):
                                nama = val
                                break
            except Exception:
                pass

        # Simpan
        if user_id and nama:
            if user_id not in kasir_dict:
                kasir_dict[user_id] = nama
            else:
                if len(nama) > len(str(kasir_dict[user_id])):
                    kasir_dict[user_id] = nama

    return kasir_dict