"""
manage_plu_view.py — Logic render halaman Manage PLU.
"""
from datetime import date

import pandas as pd
import streamlit as st

from utils.plu_loader import (
    KATEGORI,
    list_plu_files,
    save_plu_csv,
    delete_plu_file,
    load_plu_from_file,
    load_plu_by_date,
    get_stats,
)
from utils.ui_components import (
    render_header,
    render_section_title,
    metric_grid,
)


def render_manage_plu():
    render_header(
        "Manage PLU",
        "Kelola PLU untuk 4 kategori: PSM, SG, PWP, Suger",
        icon="📋",
    )

    # ---------- STATISTIK ----------
    render_section_title("Statistik", "📊")
    stats = get_stats()
    cards = []
    for kat, info in stats.items():
        cards.append({
            "label": f"{info['icon']} {info['nama']}",
            "value": f"{info['jumlah_file']} file",
            "sub": f"{info['total_plu']} PLU",
        })
    metric_grid(cards, cols=4)

    tab1, tab2, tab3 = st.tabs(["📤 Upload PLU", "📂 Daftar File", "🔍 Cek PLU Aktif"])

    # ---------- TAB 1: UPLOAD ----------
    with tab1:
        render_section_title("Upload File PLU", "📤")
        st.info("Format: **CSV, Excel (.xlsx/.xls), PDF**. Wajib ada kolom **PLU**.")

        with st.form("form_upload_plu"):
            kategori_pilihan = st.selectbox(
                "Kategori PLU:",
                options=list(KATEGORI.keys()),
                format_func=lambda x: f"{KATEGORI[x]['icon']} {KATEGORI[x]['nama']}",
                key="upload_kategori",
            )
            uploaded = st.file_uploader(
                "Pilih file (CSV / Excel / PDF)",
                type=["csv", "xlsx", "xls", "pdf"],
                key="plu_csv_upload",
            )
            col1, col2, col3 = st.columns(3)
            with col1:
                tahun = st.number_input("Tahun", min_value=2020, max_value=2100, value=date.today().year)
            with col2:
                bulan = st.number_input("Bulan", min_value=1, max_value=12, value=date.today().month)
            with col3:
                tgl_range = st.text_input("Rentang (contoh: 01_15)", value="01_15")
            submit = st.form_submit_button("🚀 Upload & Simpan", type="primary", use_container_width=True)

        if submit:
            if not uploaded:
                st.error("❌ Pilih file dulu.")
            else:
                try:
                    parts = tgl_range.strip().split("_")
                    if len(parts) != 2:
                        raise ValueError
                    tgl_awal, tgl_akhir = int(parts[0]), int(parts[1])
                except (ValueError, IndexError):
                    st.error("❌ Format rentang salah. Contoh: `01_15`")
                    st.stop()
                success, message, filepath = save_plu_csv(
                    uploaded, kategori_pilihan, tahun, bulan, tgl_awal, tgl_akhir
                )
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")

    # ---------- TAB 2: DAFTAR FILE ----------
    with tab2:
        render_section_title("Daftar File PLU", "📂")
        kategori_lihat = st.selectbox(
            "Pilih kategori:",
            options=list(KATEGORI.keys()),
            format_func=lambda x: f"{KATEGORI[x]['icon']} {KATEGORI[x]['nama']}",
            key="lihat_kategori",
        )
        files = list_plu_files(kategori_lihat)
        if not files:
            st.info(f"Belum ada file PLU untuk **{KATEGORI[kategori_lihat]['nama']}**.")
            return

        st.markdown(f"**Total {len(files)} file**")
        df_files = pd.DataFrame([
            {
                "Periode": f["periode_label"],
                "File": f["filename"],
                "Jumlah PLU": len(load_plu_from_file(f["path"])),
            }
            for f in files
        ])
        st.dataframe(df_files, use_container_width=True, hide_index=True)

        render_section_title("Hapus File", "🗑️")
        file_options = [f["filename"] for f in files]
        to_delete = st.selectbox("Pilih file:", file_options, key="plu_delete_select")
        if st.button("🗑️ Hapus File", type="secondary"):
            if delete_plu_file(kategori_lihat, to_delete):
                st.success(f"✅ File {to_delete} dihapus.")
                st.rerun()
            else:
                st.error("❌ Gagal hapus.")

        render_section_title("Preview File", "👁️")
        preview_file = st.selectbox("Pilih file:", file_options, key="plu_preview_select")
        preview_info = next((f for f in files if f["filename"] == preview_file), None)
        if preview_info:
            plu_list = load_plu_from_file(preview_info["path"])
            st.markdown(f"**Periode:** {preview_info['periode_label']}")
            st.markdown(f"**Jumlah PLU:** {len(plu_list)}")
            if plu_list:
                df_preview = pd.DataFrame(plu_list[:50])
                st.dataframe(df_preview, use_container_width=True, hide_index=True)
                if len(plu_list) > 50:
                    st.caption(f"... dan {len(plu_list) - 50} PLU lainnya")

    # ---------- TAB 3: CEK AKTIF ----------
    with tab3:
        render_section_title("Cek PLU Aktif", "🔍")
        col1, col2 = st.columns(2)
        with col1:
            kategori_cek = st.selectbox(
                "Kategori:",
                options=list(KATEGORI.keys()),
                format_func=lambda x: f"{KATEGORI[x]['icon']} {KATEGORI[x]['nama']}",
                key="cek_kategori",
            )
        with col2:
            tgl_cek = st.date_input("Tanggal:", value=date.today(), key="plu_cek_tgl")

        plu_list, file_info = load_plu_by_date(kategori_cek, tgl_cek)
        if file_info is None:
            st.warning(f"⚠️ Tidak ada file PLU **{KATEGORI[kategori_cek]['nama']}** untuk tanggal {tgl_cek}.")
        else:
            st.success(f"✅ Periode: **{file_info['periode_label']}** ({len(plu_list)} PLU)")
            if plu_list:
                df_plu = pd.DataFrame(plu_list)
                keyword = st.text_input("🔎 Cari PLU/Nama:", placeholder="Contoh: 434304 atau LEMONILO")
                if keyword:
                    keyword = str(keyword).strip().lower()
                    mask = pd.Series([False] * len(df_plu))
                    for col in df_plu.columns:
                        mask = mask | df_plu[col].astype(str).str.lower().str.contains(keyword, na=False)
                    df_plu = df_plu[mask]
                    st.caption(f"Ditemukan {len(df_plu)} PLU.")
                st.dataframe(df_plu, use_container_width=True, hide_index=True)
                st.download_button(
                    f"📥 Download PLU {KATEGORI[kategori_cek]['nama']} ({tgl_cek})",
                    data=df_plu.to_csv(index=False).encode("utf-8"),
                    file_name=f"plu_{kategori_cek}_{tgl_cek}.csv",
                    mime="text/csv",
                )
