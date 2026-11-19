"""
UI Styling, CSS theme extensions, and HTML card renderers for Streamlit.
"""

import streamlit as st

CUSTOM_CSS = """
<style>
/* Main typography and card styling */
.metric-container {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 12px 14px;
    border-left: 4px solid #1E88E5;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    margin-bottom: 12px;
    overflow: hidden;
}
.metric-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #546e7a;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.metric-value {
    font-size: clamp(1.10rem, 2.0vw, 1.35rem);
    font-weight: 700;
    color: #263238;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.25;
}
.metric-sub {
    font-size: 0.78rem;
    color: #78909c;
    margin-top: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ABCD Class Badges */
.badge-A {
    background-color: #e8f5e9;
    color: #2e7d32;
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 0.85rem;
    display: inline-block;
    border: 1px solid #a5d6a7;
}
.badge-B {
    background-color: #e3f2fd;
    color: #1565c0;
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 0.85rem;
    display: inline-block;
    border: 1px solid #90caf9;
}
.badge-C {
    background-color: #fff8e1;
    color: #f57f17;
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 0.85rem;
    display: inline-block;
    border: 1px solid #ffe082;
}
.badge-D {
    background-color: #ffebee;
    color: #c62828;
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 0.85rem;
    display: inline-block;
    border: 1px solid #ffcdd2;
}

/* Callout box for theoretical assumptions */
.assumption-box {
    background-color: #f1f8e9;
    border-left: 4px solid #7cb342;
    padding: 12px 16px;
    border-radius: 4px;
    margin: 12px 0;
    font-size: 0.90rem;
    color: #33691e;
}
.formula-box {
    background-color: #f3e5f5;
    border-left: 4px solid #8e24aa;
    padding: 12px 16px;
    border-radius: 4px;
    margin: 12px 0;
    font-size: 0.92rem;
    color: #4a148c;
}
</style>
"""


def apply_custom_styles():
    """Injects custom CSS into the Streamlit session."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, sub: str = "", border_color: str = "#1E88E5"):
    """Renders a modern metric card with subtle shadow and border accent."""
    clean_sub_text = sub.replace('"', '&quot;')
    clean_val_text = value.replace('"', '&quot;')
    clean_lbl_text = label.replace('"', '&quot;')
    card_html = f"""
    <div class="metric-container" style="border-left-color: {border_color};" title="{clean_lbl_text}: {clean_val_text}">
        <div class="metric-label" title="{clean_lbl_text}">{label}</div>
        <div class="metric-value" title="{clean_val_text}">{value}</div>
        {f'<div class="metric-sub" title="{clean_sub_text}">{sub}</div>' if sub else ''}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
