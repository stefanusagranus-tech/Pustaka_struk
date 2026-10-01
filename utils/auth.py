"""
utils/auth.py
Helper untuk login screen dengan Streamlit Secrets.
"""
import streamlit as st
import time


# ============================================================
# KONFIGURASI
# ============================================================
MAX_ATTEMPTS = 3
LOCK_DURATION = 60  # detik


# ============================================================
# AMBIL PASSWORD DARI SECRETS
# ============================================================
def get_password():
    """
    Ambil password dari Streamlit Secrets.
    Fallback ke environment variable kalau gak ada secrets.
    """
    try:
        # Cara 1: Coba ambil dari st.secrets
        if "password" in st.secrets:
            return st.secrets["password"]
    except Exception:
        pass

    # Cara 2: Fallback ke environment variable (buat dev lokal)
    import os
    return os.environ.get("APP_PASSWORD", "changeme")


# ============================================================
# SESSION STATE
# ============================================================
def init_auth_state():
    """Inisialisasi session state untuk auth."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0
    if "lock_until" not in st.session_state:
        st.session_state.lock_until = 0
    if "current_page" not in st.session_state:
        st.session_state.current_page = None


# ============================================================
# LOGIN SCREEN
# ============================================================
def render_login_screen():
    """Tampilkan login screen."""

    init_auth_state()

    # Cek lock
    if st.session_state.lock_until > time.time():
        sisa = int(st.session_state.lock_until - time.time())
        st.error(f"🔒 Terlalu banyak salah. Coba lagi dalam {sisa} detik.")
        time.sleep(1)
        st.rerun()
        return False

    # Layout login
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 40px 0 20px 0;">
            <h1 style="font-size: 3rem; margin: 0;">🎶</h1>
            <h2 style="margin: 10px 0 5px 0;">Album Lagu</h2>
            <p style="color: #888; margin: 0;">AKU YORUSHIKA. KAMU YORUSHIKA?</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        with st.form("login_form"):
            password_input = st.text_input(
                "🔑 Password",
                type="password",
                placeholder="Masukkan password...",
            )
            submit = st.form_submit_button(
                "🚀 Masuk",
                use_container_width=True,
                type="primary",
            )

        if submit:
            correct_password = get_password()

            if not correct_password or correct_password == "changeme":
                st.error("⚠️ Password belum diset. Hubungi admin.")
            elif password_input == correct_password:
                # Login sukses
                st.session_state.logged_in = True
                st.session_state.login_attempts = 0
                st.session_state.lock_until = 0
                st.success("✅ Login berhasil!")
                time.sleep(0.5)
                st.rerun()
                return True
            else:
                # Login gagal
                st.session_state.login_attempts += 1
                sisa = MAX_ATTEMPTS - st.session_state.login_attempts

                if sisa <= 0:
                    st.session_state.lock_until = time.time() + LOCK_DURATION
                    st.error(f"🔒 Terlalu banyak salah. Terkunci {LOCK_DURATION} detik.")
                else:
                    st.error(f"❌ Password salah. Sisa percobaan: {sisa}")

        st.markdown("---")
        st.caption("💡 Lupa password? Hubungi admin.")

    return False


# ============================================================
# MENU SCREEN
# ============================================================
def render_menu_screen():
    """Tampilkan menu pilih Dashboard / Idea Box."""

    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1>Selamat datang! 👋</h1>
        <p style="color: #888; font-size: 1.1rem;">Mau masuk ke mana?</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align: center; padding: 20px 0;">
                <div style="font-size: 4rem;">📊</div>
                <h2>Dashboard</h2>
                <p style="color: #888;">Analisis transaksi POS</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Fitur:**")
            st.markdown("""
            - 💰 Ringkasan omzet
            - 👤 Rekap per kasir
            - 🕐 Grafik jam ramai
            - 💳 Breakdown pembayaran
            """)

            if st.button("📊 MASUK DASHBOARD →", use_container_width=True, type="primary", key="btn_dash"):
                st.session_state.current_page = "dashboard"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align: center; padding: 20px 0;">
                <div style="font-size: 4rem;">💡</div>
                <h2>Idea Box</h2>
                <p style="color: #888;">Tulis & kelola ide proyek</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Fitur:**")
            st.markdown("""
            - ✍️ Tulis ide baru
            - 🎨 Auto-generate blueprint
            - 📋 Copy ke AI lain
            - 🗑️ Arsip ide
            """)

            if st.button("💡 MASUK IDEA BOX →", use_container_width=True, type="primary", key="btn_idea"):
                st.session_state.current_page = "idea_box"
                st.rerun()

    st.markdown("---")

    col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
    with col_l2:
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            
# ============================================================
# LOGOUT
# ============================================================
def logout():
    """Logout user."""
    st.session_state.logged_in = False
    st.session_state.login_attempts = 0
    st.session_state.lock_until = 0
    st.session_state.current_page = None
    st.rerun()


def back_to_menu():
    """Kembali ke menu pilih."""
    st.session_state.current_page = None
    st.rerun()

def render_back_to_menu_button():
    """Render tombol kembali ke menu."""
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("⬅️ Kembali ke Menu", use_container_width=True):
            back_to_menu()
