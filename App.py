import streamlit as st
import os
from utils.common import extract_zip_and_find_db

st.set_page_config(
    page_title="Dashboard POS",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Dashboard POS")
st.markdown("Upload database di bawah, lalu pilih menu di **sidebar kiri**.")

st.markdown("---")

# ============================================================
# UPLOAD DI HALAMAN UTAMA
# ============================================================
st.subheader("📁 Upload Database")

uploaded_zip = st.file_uploader(
    "Upload file ZIP database",
    type=["zip"],
    key="main_zip_uploader",
)

extract_path = "temp_dashboard_db"

if uploaded_zip is not None:
    with st.spinner("Mengekstrak & mencari database..."):
        db_path = extract_zip_and_find_db(uploaded_zip, extract_path)

    if db_path:
        st.session_state["db_path"] = db_path
        st.session_state["db_name"] = os.path.basename(db_path)
        st.success("✅ Database berhasil dibaca: **" + os.path.basename(db_path) + "**")
    else:
        st.error("❌ Tidak ada file .db di dalam ZIP.")

# Tampilkan status database
if "db_path" in st.session_state:
    st.info("📌 Database aktif: **" + st.session_state["db_name"] + "**")
    if st.button("🗑️ Hapus database (reset)"):
        st.session_state.pop("db_path", None)
        st.session_state.pop("db_name", None)
        if os.path.exists(extract_path):
            import shutil
            shutil.rmtree(extract_path, ignore_errors=True)
        st.rerun()
else:
    st.warning("⚠️ Belum ada database. Upload ZIP dulu di atas.")

st.markdown("---")

# ============================================================
# INFO HALAMAN
# ============================================================
st.markdown("### 📌 Halaman Tersedia")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📦 PSM per PLU")
    st.markdown(
        "Laporan **PSM (Promo Serba Murah)** berdasarkan daftar PLU. "
        "Menampilkan qty, sales item, dan nomor bon per PLU."
    )

with col2:
    st.markdown("#### 🎁 SG per Paket")
    st.markdown(
        "Laporan **SG (Serba Gratis)** per paket. "
        "Hanya menampilkan paket yang sudah memenuhi syarat penjualan."
    )

st.markdown("---")

st.info("💡 Buka sidebar kiri → pilih **1 PSM per PLU** atau **2 SG per Paket**.")
