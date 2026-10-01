# 📘 BLUEPRINT — Pustaka Struk v2.0

> **Blueprint resmi proyek Pustaka Struk**
> Dashboard POS Alfamart — analisis transaksi dari database SQLite

![Progress](progress_badge.svg)

---

## 🎯 1. IDENTITAS PROYEK

| Item | Detail |
|------|--------|
| **Nama** | Pustaka Struk |
| **Versi** | 2.0 |
| **Deskripsi** | Dashboard POS + analisis transaksi Alfamart |
| **Stack** | Python 3.11 + Streamlit + Pandas + SQLite |
| **Hosting** | Streamlit Cloud |
| **Repo** | `github.com/stefanusagranus-tech/Pustaka_struk` |
| **Status** | 🟡 In Development |

---

## 🎯 2. TUJUAN

Membangun **dashboard anonim** untuk menganalisis data POS dari file SQLite (`.db`), mencakup:

1. ✅ Upload database ZIP → auto-extract
2. ✅ Analisis omzet, struk, item
3. ✅ Rekap per kasir
4. ✅ Breakdown pembayaran (cash, debit, e-wallet)
5. ✅ Grafik jam ramai
6. ✅ Fitur Idea Box (tulis ide → auto-generate blueprint)
7. ✅ Auto-progress tracker
8. ⏳ Modul analisis lanjutan (M1-M7)
9. ⏳ Dokumentasi lengkap

---

## 🏗️ 3. ARSITEKTUR

### 3.1 Struktur Folder

```

pustaka_struk/
├── .github/
│   └── workflows/
│       └── check-progress.yml
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
│   ├── init.py
│   ├── anonim.py
│   ├── common.py
│   └── plu_dict.py
├── App.py
├── requirements.txt
└── README.md

```

### 3.2 Diagram Arsitektur

```mermaid
flowchart TB
    subgraph Input
        ZIP[ZIP Database]
    end
    
    subgraph Core
        EXTRACT[extract_zip_and_find_db]
        DB[(SQLite .db)]
        LOAD[load_tables]
    end
    
    subgraph Utils
        U1[utils/anonim.py]
        U2[utils/common.py]
        U3[utils/plu_dict.py]
    end
    
    subgraph Pages
        P1[App.py]
        P2[0_Home.py]
        P3[0b_Idea_Box.py]
        P4[1-6 Halaman]
    end
    
    subgraph Docs
        D1[progress.json]
        D2[BLUEPRINT.md]
        D3[ideas.json]
    end
    
    subgraph Automation
        GHA[GitHub Actions]
        SCAN[check_progress.py]
    end
    
    ZIP --> EXTRACT
    EXTRACT --> DB
    DB --> LOAD
    LOAD --> P1
    LOAD --> P4
    U1 --> P1
    U1 --> P2
    U1 --> P3
    U2 --> P1
    P3 --> D3
    SCAN --> D1
    SCAN --> D2
    GHA --> SCAN
    
    style ZIP fill:#4CAF50,color:#fff
    style DB fill:#2196F3,color:#fff
    style P1 fill:#FF9800,color:#fff
    style GHA fill:#9C27B0,color:#fff
---

## 🗄️ 4. SKEMA DATABASE

File `.db` (SQLite) berisi ~29 tabel:

### 4.1 Tabel yang Dipakai (5)
| Tabel | Fungsi |
|-------|--------|
| `tx_tsale` | Header penjualan |
| `tx_tsale_card` | Kartu debit |
| `tx_trans` | Detail item |
| `log_receipt_prn` | Data struk |
| `tx_trans_non_commerce` | Non-commerce |

### 4.2 Tabel Belum Dipakai (24)
- **Promo:** `log_promo_*` (5 tabel)
- **E-Money:** `log_wallet`, `log_wallet_qr`
- **Voucher:** `log_con_voucher`, `temp_voucher`
- **Kasir:** `log_cashier`, `log_eod`, `log_login_pos`
- **Sync/Debug:** `log_error`, `log_trans_sync`, `log_connection`

---

## 📋 5. ROADMAP FASE

| No | Fase | Deskripsi | Estimasi | Status |
|----|------|-----------|:--------:|:------:|
| 0 | Setup | Refactor utils | 1 hari | ⬜ |
| 1 | Fix App.py | Bug fix + anonim | 2 hari | ⬜ |
| 2 | Home | Pusat navigasi | 1 hari | ⬜ |
| 3 | Idea Box | Tulis ide | 2 hari | ⬜ |
| 4 | Progress Tracker | Auto-scan | 1 hari | ⬜ |
| 5 | M1 Transaction | Analisis detail | 3 hari | ⬜ |
| 6 | M2 Promo | Analisis promo | 3 hari | ⬜ |
| 7 | M3 Payment | Analisis bayar | 2 hari | ⬜ |
| 8 | M4 Customer | Analisis member | 2 hari | ⬜ |
| 9 | M5 Kasir | Analisis kasir | 2 hari | ⬜ |
| 10 | M6 Print | Audit printing | 1 hari | ⬜ |
| 11 | M7 Monitor | Monitoring | 2 hari | ⬜ |
| 12 | Docs | Dokumentasi | 1 hari | ⬜ |
| 13 | Deploy | Push + uji | 1 hari | ⬜ |

**Total:** ~24 hari kerja

> **Note:** Status di atas auto-update via `scripts/check_progress.py`

---

## 🎨 6. STYLE GUIDE

### 6.1 Anonim
Semua halaman **WAJIB** pakai `setup_anonim_page()`:
```python
from utils.anonim import setup_anonim_page, render_nav_universal, apply_nav_style

---

## 🤖 7. WORKFLOW OTOMATIS

### 7.1 Auto-Scan Progress

Setiap push ke GitHub:

```mermaid
flowchart LR
    A[Push ke GitHub] --> B[GitHub Actions trigger]
    B --> C[Run check_progress.py]
    C --> D[Update progress.json]
    D --> E[Update PROGRESS_REPORT.md]
    E --> F[Update progress_badge.svg]
    F --> G[Commit balik ke repo]
    G --> H[Badge and report auto-update]
    
    style A fill:#4CAF50,color:#fff
    style H fill:#2196F3,color:#fff

setup_anonim_page("Judul Halaman", "📊")
apply_nav_style()

render_nav_universal("id_halaman")
