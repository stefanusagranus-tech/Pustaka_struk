# BLUEPRINT - Pustaka Struk v2.0

Blueprint resmi proyek Pustaka Struk.
Dashboard - analisis transaksi dari database SQLite.

## 1. IDENTITAS PROYEK

- Nama: Pustaka Struk
- Versi: 2.0
- Deskripsi: Dashboardh dan Analisis
- Stack: Python 3.11 + Streamlit + Pandas + SQLite
- Hosting: Streamlit Cloud
- Repo: github.com/stefanusagranus-tech/Pustaka_struk
- Status: In Development

## 2. TUJUAN

Membangun dashboard anonim untuk menganalisis data dari file SQLite (.db), mencakup:

1. Upload database ZIP - auto-extract
2. Analisis omzet, struk, item
3. Rekap per kasir
4. Breakdown pembayaran (cash, debit, e-wallet)
5. Grafik jam ramai
6. Fitur Idea Box (tulis ide - auto-generate blueprint)
7. Auto-progress tracker
8. Modul analisis lanjutan (M1-M7)
9. Dokumentasi lengkap

## 3. ARSITEKTUR

### 3.1 Struktur Folder

    pustaka_struk/
    ├── .github/workflows/check-progress.yml
    ├── docs/
    │   ├── BLUEPRINT.md
    │   ├── progress.json
    │   ├── PROGRESS_REPORT.md
    │   ├── progress_badge.svg
    │   ├── ideas.json
    │   └── ideas_archive.json
    ├── pages/
    │   ├── 0_Home.py
    │   ├── 0b_Idea_Box.py
    │   ├── 1_PSM_per_PLU.py
    │   ├── 2_SG_per_Paket.py
    │   ├── 3_struk_Suger.py
    │   ├── 5_Topup_Flaz.py
    │   └── 6_Cek_Struk_Void.py
    ├── scripts/
    │   ├── check_progress.py
    │   └── migrate_pages.py
    ├── utils/
    │   ├── __init__.py
    │   ├── anonim.py
    │   ├── common.py
    │   └── plu_dict.py
    ├── App.py
    ├── requirements.txt
    └── README.md

### 3.2 Komponen Utama

- App.py - Dashboard utama
- pages/0_Home.py - Pusat navigasi
- pages/0b_Idea_Box.py - Tulis ide
- pages/1-6_*.py - Halaman analisis (PSM, SG, Struk, Topup, Void)
- utils/anonim.py - CSS + navigasi helper
- utils/common.py - Load SQLite helper
- utils/plu_dict.py - Mapping PLU
- scripts/check_progress.py - Auto-scan progress
- scripts/migrate_pages.py - Auto-migrate anonim
- .github/workflows/check-progress.yml - CI/CD auto-scan

### 3.3 Teknologi Stack

- Bahasa: Python 3.11+
- Framework UI: Streamlit (min 1.30)
- Data: Pandas 2.1+
- Database: SQLite (built-in)
- Chart: Streamlit native
- Deploy: Streamlit Cloud
- CI/CD: GitHub Actions
- Version Control: Git + GitHub

## 4. SKEMA DATABASE

File .db (SQLite) berisi sekitar 29 tabel.

### 4.1 Tabel yang Dipakai (5)

- tx_tsale - Header penjualan
- tx_tsale_card - Kartu debit
- tx_trans - Detail item
- log_receipt_prn - Data struk
- tx_trans_non_commerce - Non-commerce

### 4.2 Tabel Belum Dipakai (24)

- Promo: log_promo_* (5 tabel)
- E-Money: log_wallet, log_wallet_qr
- Voucher: log_con_voucher, temp_voucher
- Kasir: log_cashier, log_eod, log_login_pos
- Sync/Debug: log_error, log_trans_sync, log_connection

## 5. ROADMAP FASE

| No | Fase | Deskripsi | Estimasi | Status |
|----|------|-----------|:--------:|:------:|
| 0 | Setup | Refactor utils | 1 hari | belum |
| 1 | Fix App.py | Bug fix + anonim | 2 hari | belum |
| 2 | Home | Pusat navigasi | 1 hari | belum |
| 3 | Idea Box | Tulis ide | 2 hari | belum |
| 4 | Progress Tracker | Auto-scan | 1 hari | belum |
| 5 | M1 Transaction | Analisis detail | 3 hari | belum |
| 6 | M2 Promo | Analisis promo | 3 hari | belum |
| 7 | M3 Payment | Analisis bayar | 2 hari | belum |
| 8 | M4 Customer | Analisis member | 2 hari | belum |
| 9 | M5 Kasir | Analisis kasir | 2 hari | belum |
| 10 | M6 Print | Audit printing | 1 hari | belum |
| 11 | M7 Monitor | Monitoring | 2 hari | belum |
| 12 | Docs | Dokumentasi | 1 hari | belum |
| 13 | Deploy | Push + uji | 1 hari | belum |

Total: sekitar 24 hari kerja.

Status di atas auto-update via scripts/check_progress.py

## 6. STYLE GUIDE

### 6.1 Anonim

Semua halaman wajib pakai setup_anonim_page():

    from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style
    setup_anonim_page("Judul Halaman", "emoji")
    apply_nav_style()

### 6.2 Navigasi

Setiap halaman punya tombol navigasi di bawah:

    render_nav_universal("id_halaman")

ID yang tersedia: home, idea, dashboard, psm, sg, topup, struk, void

### 6.3 Cache

Gunakan @st.cache_data untuk load database:

    @st.cache_data(show_spinner=False)
    def get_data(db_path):
        return load_tables(db_path, TABLES)

### 6.4 Format Rupiah

    "Rp " + format(angka, ",.0f")

### 6.5 Bahasa

- Bahasa Indonesia santai tapi jelas
- Emoji secukupnya (max 2 per baris)
- Langsung to the point

### 6.6 Struktur File Halaman

    # 1. Import
    import streamlit as st
    import pandas as pd
    from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style
    from utils.common import load_tables

    # 2. Setup anonim (PALING ATAS)
    setup_anonim_page("Judul", "emoji")
    apply_nav_style()

    # 3. Header
    st.title("Judul Halaman")
    st.markdown("Deskripsi")

    # 4. Load data
    # ...

    # 5. Konten utama
    # ...

    # 6. Navigasi (PALING BAWAH)
    render_nav_universal("id_halaman")

## 7. WORKFLOW OTOMATIS

### 7.1 Auto-Scan Progress

Setiap push ke GitHub:
- GitHub Actions trigger
- Run check_progress.py
- Update progress.json
- Update PROGRESS_REPORT.md
- Update progress_badge.svg
- Commit balik ke repo

File yang auto-update:
- docs/progress.json
- docs/PROGRESS_REPORT.md
- docs/progress_badge.svg

### 7.2 Idea Box Workflow

- Tulis ide
- Save ke ideas.json
- Auto-generate blueprint .md
- Copy blueprint
- Paste ke AI lain
- AI kasih kode
- Implement
- Push ke GitHub
- Auto-update progress

### 7.3 Manual Scan via Termux

    cd ~/Pustaka_struk
    python scripts/check_progress.py --report

## 8. CHECKLIST PER FASE

### Fase 0 - Setup
- [ ] utils/anonim.py dibuat
- [ ] utils/common.py dirapikan
- [ ] requirements.txt di-pin

### Fase 1 - Fix App.py
- [ ] Import anonim ditambah
- [ ] setup_anonim_page dipanggil
- [ ] render_nav_universal di bawah
- [ ] Error handling OK

### Fase 2 - Home
- [ ] pages/0_Home.py dibuat
- [ ] Kartu menu ada
- [ ] Navigasi jalan

### Fase 3 - Idea Box
- [ ] pages/0b_Idea_Box.py dibuat
- [ ] Tab Tambah / Daftar / Arsip
- [ ] Auto-generate blueprint
- [ ] Copy ke AI jalan

### Fase 4 - Progress Tracker
- [ ] scripts/check_progress.py dibuat
- [ ] docs/progress.json ada
- [ ] GitHub Actions jalan
- [ ] Badge muncul

### Fase 5-11 - Modul M1-M7
- [ ] M1 Transaction
- [ ] M2 Promo
- [ ] M3 Payment
- [ ] M4 Customer
- [ ] M5 Kasir
- [ ] M6 Print
- [ ] M7 Monitor

### Fase 12 - Docs
- [x] docs/BLUEPRINT.md (file ini)
- [x] README.md
- [ ] docs/USER_GUIDE.md

### Fase 13 - Deploy
- [ ] Semua push ke GitHub
- [ ] Streamlit Cloud OK
- [ ] docs/DEPLOY_SUCCESS.md

## 9. REFERENSI

- Streamlit Docs: https://docs.streamlit.io
- Pandas Docs: https://pandas.pydata.org/docs
- SQLite Docs: https://sqlite.org/docs.html
- Mermaid Docs: https://mermaid.js.org

## 10. NEXT ACTION

Fase berikutnya: lihat docs/PROGRESS_REPORT.md

Cara mulai:
1. Cek docs/progress.json - lihat fase yang belum selesai
2. Buka pages/ - cek file yang belum ada
3. Kalau ada ide baru - tulis di Idea Box
4. Copy blueprint - paste ke AI lain
5. Implement - push ke GitHub
6. Auto-update - progress tracker jalan otomatis

## 11. TROUBLESHOOTING

### Error: ModuleNotFoundError No module named 'utils'
Solusi: Pastikan utils/__init__.py ada (boleh kosong).

### Error: ImportError cannot import name 'render_nav_universal'
Solusi: Update utils/anonim.py dengan versi lengkap.

### Error: Sidebar gak muncul
Solusi: Pakai tombol navigasi custom (render_nav_universal).

### Error: GitHub Actions gagal
Solusi:
1. Cek tab Actions di GitHub
2. Klik workflow yang gagal
3. Lihat log error
4. Fix di kode - push ulang

## 12. KONTAK

- Owner: stefanusagranus-tech
- Repo: github.com/stefanusagranus-tech/Pustaka_struk
- Deploy: Streamlit Cloud
- Status: Internal use only

---

Dokumen ini auto-scan oleh scripts/check_progress.py
Jangan edit manual bagian Status di roadmap - biar auto-update tetap sinkron.
Terakhir update: Auto-generated
Versi blueprint: 2.0
