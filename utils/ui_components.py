"""
ui_components.py — Komponen UI reusable untuk Pustaka Struk.
"""
import streamlit as st


def render_header(title: str, subtitle: str = "", icon: str = "📦"):
    """Header aplikasi (dipakai di semua halaman)."""
    st.markdown(
        f"""
        <div class="app-header">
            <div>
                <h1>{icon} {title}</h1>
                {f'<p>{subtitle}</p>' if subtitle else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(text: str, icon: str = ""):
    """Judul section dengan garis bawah."""
    st.markdown(
        f'<div class="section-title">{icon} {text}</div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, sub: str = "", variant: str = ""):
    """Kartu metrik (pengganti st.metric default)."""
    variant_class = f" {variant}" if variant else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value{variant_class}">{value}</div>
            {f'<div class="sub">{sub}</div>' if sub else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_grid(cards: list, cols: int = 3):
    """
    Render grid metric card.
    cards: list of dict {label, value, sub (opt), variant (opt)}
    """
    for i in range(0, len(cards), cols):
        row = st.columns(cols)
        for j, card in enumerate(cards[i:i + cols]):
            with row[j]:
                metric_card(
                    card.get("label", ""),
                    card.get("value", ""),
                    card.get("sub", ""),
                    card.get("variant", ""),
                )


def render_pill(text: str, variant: str = ""):
    """Badge kecil."""
    cls = f"pill {variant}" if variant else "pill"
    return f'<span class="{cls}">{text}</span>'


def render_card(content_html: str):
    """Card generic untuk konten HTML."""
    st.markdown(f'<div class="card">{content_html}</div>', unsafe_allow_html=True)


def render_footer():
    """Footer konsisten."""
    st.markdown("---")
    st.caption("Pustaka Struk v2.0 — Internal use only")
