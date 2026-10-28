"""
Modern aesthetic design system and custom styling for FailureForensicsTool.
"""

import streamlit as st


def inject_custom_styles():
    """Inject premium CSS styling into Streamlit app."""
    custom_css = """
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    code, pre, [class*="stCode"] {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px;
    }

    /* Gradient Main Headers */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin-bottom: 0.5rem !important;
    }

    h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #f1f5f9 !important;
    }

    /* Glassmorphic Metric Cards */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.65) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        padding: 1.1rem 1.3rem !important;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.35) !important;
        backdrop-filter: blur(12px) !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4) !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #94a3b8 !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
    }

    /* Custom Stepper Chips */
    .step-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.45rem 0.9rem;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #e2e8f0;
    }

    .step-chip.active {
        border-color: #38bdf8;
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.35);
    }

    .step-chip.failed {
        border-color: #f87171;
        background: rgba(248, 113, 113, 0.15);
        color: #f87171;
    }

    .step-chip.success {
        border-color: #4ade80;
        background: rgba(74, 222, 128, 0.15);
        color: #4ade80;
    }

    /* Template Cards */
    .preset-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 10px;
        padding: 0.85rem;
        margin-bottom: 0.6rem;
        cursor: pointer;
        transition: background 0.15s ease;
    }

    .preset-card:hover {
        background: rgba(51, 65, 85, 0.7);
        border-color: rgba(99, 102, 241, 0.4);
    }

    /* Modern Primary Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4) !important;
        transition: all 0.2s ease !important;
    }

    button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.6) !important;
    }

    /* Subtle Dividers */
    hr {
        border-color: rgba(255, 255, 255, 0.07) !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
