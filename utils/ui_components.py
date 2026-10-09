"""
ui_components.py — Komponen UI reusable untuk Pustaka Struk.
Dibuat ulang: lengkap, konsisten, backward-compatible.
"""
from __future__ import annotations

import streamlit as st


# ============================================================
# HEADER
# ============================================================
def render_page_header(
    title: str,
    subtitle: str = "",
    icon: str = "📦",
) -> None:
    """
    Header halaman utama (dipakai di semua pages).
    Contoh:
        render_page_header("Cek Struk Detail", "Lihat detail transaksi", icon="🔍")
    """
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="app-header">
            <div>
                <h1>{icon} {title}</h1>
                {subtitle_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Alias lama — agar kode yang masih pakai render_header tetap jalan
def render_header(title: str, subtitle: str = "", icon: str = "📦") -> None:
    """Alias dari render_page_header (backward compatibility)."""
    render_page_header(title, subtitle, icon)


# ============================================================
# SECTION TITLE
# ============================================================
def render_section_title(text: str, icon: str = "") -> None:
    """
    Judul section dengan garis bawah.
    Contoh:
        render_section_title("Info Struk", "🧾")
    """
    prefix = f"{icon} " if icon else ""
    st.markdown(
        f'<div class="section-title">{prefix}{text}</div>',
        unsafe_allow_html=True,
    )


def render_divider() -> None:
    """Garis pemisah konsisten."""
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ============================================================
# METRIC CARD
# ============================================================
def metric_card(
    label: str,
    value: str,
    sub: str = "",
    variant: str = "",
) -> None:
    """
    Kartu metrik tunggal (pengganti st.metric default).
    variant: "" | "accent" | "success" | "warning" | "danger"
    """
    variant_class = f" {variant}" if variant else ""
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value{variant_class}">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_grid(cards: list, cols: int = 3) -> None:
    """
    Render grid metric card dalam beberapa kolom.
    cards: list of dict {label, value, sub (opt), variant (opt)}
    Contoh:
        metric_grid([
            {"label": "Total", "value": "Rp 100.000", "variant": "success"},
            {"label": "Qty",   "value": "12"},
        ], cols=2)
    """
    if not cards:
        return
    cols = max(1, int(cols))
    for i in range(0, len(cards), cols):
        row = st.columns(cols)
        for j, card in enumerate(cards[i : i + cols]):
            with row[j]:
                metric_card(
                    card.get("label", ""),
                    card.get("value", ""),
                    card.get("sub", ""),
                    card.get("variant", ""),
                )


# ============================================================
# PILL / BADGE
# ============================================================
def render_pill(text: str, variant: str = "") -> str:
    """
    Mengembalikan HTML badge kecil (bukan render langsung).
    Pemakaian:
        st.markdown(render_pill("Sukses", "success"), unsafe_allow_html=True)
    """
    cls = f"pill {variant}" if variant else "pill"
    return f'<span class="{cls}">{text}</span>'


def render_badge(text: str, variant: str = "") -> None:
    """Render badge langsung (tanpa perlu st.markdown manual)."""
    st.markdown(render_pill(text, variant), unsafe_allow_html=True)


# ============================================================
# CARD GENERIC
# ============================================================
def render_card(content_html: str) -> None:
    """Card generic untuk konten HTML bebas."""
    st.markdown(
        f'<div class="card">{content_html}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# INFO BOXES (opsional, kalau dipakai di halaman lain)
# ============================================================
def render_info(text: str, icon: str = "ℹ️") -> None:
    """Info box dengan ikon."""
    st.info(f"{icon} {text}")


def render_warning(text: str, icon: str = "⚠️") -> None:
    """Warning box dengan ikon."""
    st.warning(f"{icon} {text}")


def render_success(text: str, icon: str = "✅") -> None:
    """Success box dengan ikon."""
    st.success(f"{icon} {text}")


def render_error(text: str, icon: str = "❌") -> None:
    """Error box dengan ikon."""
    st.error(f"{icon} {text}")


# ============================================================
# FOOTER
# ============================================================
def render_footer(
    text: str = "Pustaka Struk v2.0 — Internal use only",
) -> None:
    """Footer konsisten di semua halaman."""
    st.markdown("---")
    st.caption(text)


# ============================================================
# NAVIGASI BAWAH (opsional, sering dipakai)
# ============================================================
def render_back_button(
    label: str = "🏠 Kembali ke Menu Utama",
    page: str = "App.py",
    key: str = "back_to_menu",
) -> None:
    """
    Tombol kembali ke menu utama (rata tengah).
    """
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(label, use_container_width=True, key=key):
            st.switch_page(page)


# ============================================================
# EXPORTS (biar jelas apa yang tersedia)
# ============================================================
__all__ = [
    # header & layout
    "render_page_header",
    "render_header",
    "render_section_title",
    "render_divider",
    # metrik
    "metric_card",
    "metric_grid",
    # badge / pill
    "render_pill",
    "render_badge",
    # card
    "render_card",
    # info boxes
    "render_info",
    "render_warning",
    "render_success",
    "render_error",
    # footer & navigasi
    "render_footer",
    "render_back_button",
]
