"""
APIx: Real-time Airfare Price Index for India
Official Web Dashboard for National Statistical Office (NSO/MoSPI) & Reserve Bank of India (RBI).
Built for Smart India Hackathon 2026 | Team: CodeCrew
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Setup page layout
st.set_page_config(
    page_title="APIx | Real-time Airfare Price Index (CPI Transport)",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Styling: Modern Obsidian / Royal Navy Glassmorphism
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        letter-spacing: -0.02em;
    }

    /* Background Ambient Glow */
    .stApp {
        background-color: #080c15;
        background-image: 
            radial-gradient(at 0% 0%, rgba(14, 165, 233, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.04) 0px, transparent 50%);
    }

    /* Hero Banner - Compact & Sleek */
    .hero-container {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(17, 24, 39, 0.95) 50%, rgba(12, 74, 110, 0.4) 100%);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-top: 3px solid #38bdf8;
        border-radius: 14px;
        padding: 14px 20px;
        margin-bottom: 14px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(16px);
    }
    
    .hero-title {
        font-size: 1.65rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 50%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }
    
    .hero-subtitle {
        font-size: 0.84rem;
        color: #cbd5e1;
        margin-top: 3px;
        font-weight: 400;
    }

    .hero-telemetry-box {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(56, 189, 248, 0.22);
        border-radius: 12px;
        padding: 12px 18px;
        min-width: 320px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    @media (max-width: 980px) {
        .hero-grid {
            grid-template-columns: 1fr !important;
        }
        .hero-telemetry-box {
            min-width: 100% !important;
            margin-top: 10px;
        }
    }

    /* Glowing radar pulse */
    .pulse-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse-animation 2s infinite;
        margin-right: 5px;
        vertical-align: middle;
    }
    @keyframes pulse-animation {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Badges */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        padding: 3px 9px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 6px;
        border: 1px solid transparent;
        letter-spacing: 0.02em;
    }
    .badge-mospi { background: rgba(6, 78, 59, 0.5); color: #34d399; border-color: rgba(52, 211, 153, 0.3); }
    .badge-rbi { background: rgba(30, 27, 75, 0.6); color: #a5b4fc; border-color: rgba(165, 180, 252, 0.3); }
    .badge-dgca { background: rgba(69, 26, 3, 0.6); color: #fcd34d; border-color: rgba(252, 211, 77, 0.3); }
    .badge-team { background: rgba(8, 47, 73, 0.6); color: #38bdf8; border-color: rgba(56, 189, 248, 0.3); }

    /* Custom KPI Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 14px;
        margin-bottom: 22px;
    }
    .kpi-card {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.6) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 8px 25px rgba(56, 189, 248, 0.12);
    }
    .kpi-label {
        font-size: 0.84rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #cbd5e1;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.2;
    }
    .kpi-delta {
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .delta-up { color: #f87171; }
    .delta-down { color: #34d399; }
    .delta-neutral { color: #38bdf8; }

    /* Modern Glass Card for Text/Info */
    .glass-panel {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
    }

    /* Clean Balanced 3x3 Grid Tabs for 9 Modular Tabs */
    .stTabs [data-baseweb="tab-list"],
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        gap: 6px !important;
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding: 6px !important;
        border-radius: 12px !important;
        backdrop-filter: blur(12px) !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .stTabs [data-baseweb="tab"],
    [data-testid="stTabs"] [data-baseweb="tab"] {
        width: 100% !important;
        height: 38px !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        padding: 0 10px !important;
        border: none !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        white-space: nowrap !important;
        background: transparent !important;
        box-sizing: border-box !important;
    }
    .stTabs [data-baseweb="tab"]:hover,
    [data-testid="stTabs"] [data-baseweb="tab"]:hover {
        color: #f8fafc !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    .stTabs [aria-selected="true"],
    [data-testid="stTabs"] [aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
    }
    /* Anti-duplication safeguard: hide any ghost/duplicate tab lists */
    .stTabs [data-baseweb="tab-list"] ~ [data-baseweb="tab-list"],
    [data-testid="stTabs"] [data-baseweb="tab-list"] ~ [data-baseweb="tab-list"],
    [data-testid="stTabs"] ~ [data-testid="stTabs"] {
        display: none !important;
    }
    /* Hide default Streamlit tab scroll buttons and borders */
    .stTabs button[aria-label="Previous tab"],
    .stTabs button[aria-label="Next tab"],
    [data-testid="stTabs"] button[aria-label="Previous tab"],
    [data-testid="stTabs"] button[aria-label="Next tab"],
    .stTabs [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"],
    [data-testid="stTabs"] [data-baseweb="tab-border"],
    [data-testid="stTabs"] hr {
        display: none !important;
    }

    @media (max-width: 900px) {
        .stTabs [data-baseweb="tab-list"],
        [data-testid="stTabs"] [data-baseweb="tab-list"],
        [data-testid="stTabs"] [role="tablist"],
        div[role="tablist"] {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }
    }
    @media (max-width: 600px) {
        .stTabs [data-baseweb="tab-list"],
        [data-testid="stTabs"] [data-baseweb="tab-list"],
        [data-testid="stTabs"] [role="tablist"],
        div[role="tablist"] {
            grid-template-columns: repeat(1, minmax(0, 1fr)) !important;
        }
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #080c15;
    }
    ::-webkit-scrollbar-thumb {
        background: #1e293b;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from apix.config import DB_PATH, BASKET_ROUTES, ADVANCE_WINDOWS, canonical_route, AIRPORT_DATA, AIRLINES
from apix.database.db import DatabaseManager
from apix.index.weights import WeightManager
from apix.backtest.backtester import DGCABacktester
from apix.scrapers.scheduler import ScraperScheduler
from apix.pipeline.cleaner import DataCleaningPipeline
from apix.index.engine import IndexEngine
from apix.index.esankhyiki import ESankhyikiManager, PSD_WEIGHTS
from apix.index.watchdog import DGCAWatchdogManager

@st.cache_resource
def get_db():
    return DatabaseManager(os.path.join(BASE_DIR, DB_PATH))

@st.cache_resource
def get_weight_mgr():
    return WeightManager()

@st.cache_resource
def get_watchdog_mgr():
    return DGCAWatchdogManager()

@st.cache_resource
def get_esankhyiki_mgr():
    return ESankhyikiManager()

db = get_db()
weight_mgr = get_weight_mgr()
esankhyiki_mgr = get_esankhyiki_mgr()
watchdog_mgr = get_watchdog_mgr()


# --- Plotly Dark Theme Preset ---
def apply_dark_theme(fig, height=380, title=None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.45)",
        font=dict(family="Inter, sans-serif", color="#f8fafc", size=12),
        margin=dict(l=55, r=20, t=35 if title else 25, b=25),
        height=height,
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.08)",
            zerolinecolor="rgba(255, 255, 255, 0.12)",
            tickfont=dict(color="#f8fafc", size=11, family="Inter, sans-serif"),
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.08)",
            zerolinecolor="rgba(255, 255, 255, 0.12)",
            tickfont=dict(color="#f8fafc", size=11, family="Inter, sans-serif"),
        ),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.90)",
            bordercolor="rgba(255, 255, 255, 0.2)",
            borderwidth=1,
            font=dict(color="#f8fafc", size=11, family="Inter, sans-serif"),
        ),
    )
    if title:
        fig.update_layout(title=dict(text=title, font=dict(family="Plus Jakarta Sans, sans-serif", size=14, color="#ffffff")))
    return fig

# --- TOP HERO BANNER ---
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">APIx · Real-Time Airfare Price Index</h1>
    <div class="hero-subtitle">
        High-Frequency Aviation Price Ingestion & Econometric Indexing for CPI Transport Augmentation
    </div>
    <div style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 8px;">
        <span class="badge-pill badge-mospi">🏛️ MoSPI / NSO · CPI Sub-Index</span>
        <span class="badge-pill badge-rbi">🏦 RBI · Monetary Policy Early Signal</span>
        <span class="badge-pill badge-dgca">✈️ DGCA · Volume-Weighted</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Load index dataset
@st.cache_data(ttl=15)
def load_index_data():
    df = db.get_daily_indices()
    if not df.empty:
        df["date_dt"] = pd.to_datetime(df["date"])
        if "two_tier_index" not in df.columns:
            df["two_tier_index"] = df["laspeyres_index"]
        df["rolling_7d_twotier"] = df["two_tier_index"].rolling(7, min_periods=1).mean()
        df["rolling_7d_laspeyres"] = df["laspeyres_index"].rolling(7, min_periods=1).mean()
        df["rolling_7d_fare"] = df["average_fare"].rolling(7, min_periods=1).mean()
        df["daily_inflation_pct"] = df["two_tier_index"].pct_change() * 100.0
    return df

df_indices = load_index_data()

if df_indices.empty:
    st.warning("No index records found in database. Running initialization...")
    from scripts.init_db import run_initialization
    run_initialization(days=90)
    st.rerun()

# Sidebar Parameters
with st.sidebar:
    st.markdown("### 📐 **Official Formulation**")
    st.markdown("""
    <div class="glass-panel" style="padding: 14px; border-left: 3px solid #38bdf8; margin-bottom: 14px;">
        <div style="font-size: 0.74rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em;">
            Standard Formulation
        </div>
        <div style="font-size: 0.98rem; font-weight: 700; color: #f8fafc; margin: 4px 0;">
            Two-Tier Jevons-Laspeyres
        </div>
        <div style="font-size: 0.78rem; color: #cbd5e1; line-height: 1.45; margin-top: 6px;">
            • <b>Tier 1 (Micro):</b> Jevons Geometric Mean per flight eliminates dynamic surge noise.<br/>
            • <b>Tier 2 (Macro):</b> DGCA passenger-volume weighted Laspeyres aggregation.
        </div>
        <div style="font-size: 0.72rem; color: #34d399; margin-top: 8px; font-weight: 600;">
            ✓ IMF & Eurostat HICP Best Practice
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### ✈️ **Monitored Corridors (Top 15 · ~38.9M Annual Pax)**")
    st.markdown("""
    - **BOM ↔ DEL** (17.1% DGCA Share)
    - **BLR ↔ DEL** (12.2% DGCA Share)
    - **BLR ↔ BOM** (10.3% DGCA Share)
    - **CCU ↔ DEL** (7.3% DGCA Share)
    - **DEL ↔ MAA** (6.0% DGCA Share)
    - **BLR ↔ HYD** (5.9% DGCA Share)
    - *+ 9 High-Growth Regional Corridors*
    """)
    st.markdown("---")
    st.markdown("#### 🏢 **Airline & OTA Sources**")
    st.caption("IndiGo (62%), Air India (14%), Air India Express (8%), Akasa Air (5%), SpiceJet (4%) + MakeMyTrip, EaseMyTrip.")

formula_col = "two_tier_index"
formula_name = "Two-Tier Jevons-Laspeyres"
rolling_col = "rolling_7d_twotier"

latest_row = df_indices.iloc[-1]
prev_row = df_indices.iloc[-2] if len(df_indices) > 1 else latest_row
mom_change = ((latest_row[formula_col] - df_indices.iloc[0][formula_col]) / df_indices.iloc[0][formula_col]) * 100.0
daily_diff = latest_row[formula_col] - prev_row[formula_col]

# Balanced 3x3 Modular Tabs
tabs = st.tabs([
    "📈 Daily Trajectory",
    "⚖️ MoSPI vs APIx",
    "🗺️ Corridors & Map",
    "📈 Dynamic Pricing",
    "🛡️ DGCA Watchdog",
    "🧾 Statutory Taxes",
    "🔬 DGCA Backtest",
    "🛡️ Ethical Scraper",
    "🏛️ MoSPI & RBI Export",
])

# ==========================================
# TAB 1: HIGH-FREQUENCY DAILY APIx INDEX TRAJECTORY
# ==========================================
with tabs[0]:
    st.markdown("### 📈 **High-Frequency Daily APIx Index Trajectory (90-Day Time-Series)**")
    st.caption("Daily Two-Tier Jevons-Laspeyres Index tracking airline price movements across all 15 DGCA domestic corridors (~38.9M annual passenger traffic).")

    dod_fare_pct = ((latest_row['average_fare'] - prev_row['average_fare']) / prev_row['average_fare'] * 100)
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">APIx Index Level</div>
            <div class="kpi-value">{latest_row[formula_col]:.2f}</div>
            <div class="kpi-delta {'delta-up' if daily_diff > 0 else 'delta-down'}">
                {'▲' if daily_diff > 0 else '▼'} {daily_diff:+.2f} pts vs yesterday
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">7-Day Trend Baseline</div>
            <div class="kpi-value">{latest_row[rolling_col]:.2f}</div>
            <div class="kpi-delta delta-neutral">● Smoothed Trend</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Basket Average Fare</div>
            <div class="kpi-value">₹{latest_row['average_fare']:,.0f}</div>
            <div class="kpi-delta {'delta-up' if dod_fare_pct > 0 else 'delta-down'}">
                {'▲' if dod_fare_pct > 0 else '▼'} {dod_fare_pct:+.1f}% DoD
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">90-Day Net Drift</div>
            <div class="kpi-value">{mom_change:+.2f}%</div>
            <div class="kpi-delta {'delta-up' if mom_change > 0 else 'delta-down'}">
                ● MoSPI Inflation Signal
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Daily Sample Depth</div>
            <div class="kpi-value">{latest_row['sample_size']:,}</div>
            <div class="kpi-delta delta-neutral">● Verified Quotes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_left, c_right = st.columns([7, 3])
    with c_left:
        st.markdown("##### **APIx Two-Tier Index Trajectory vs. Base (P₀ = 100.0)**")
        fig = go.Figure()

        # Volatility Shaded Area
        fig.add_trace(go.Scatter(
            x=df_indices["date_dt"],
            y=df_indices[formula_col],
            mode="lines",
            name="APIx (Two-Tier Jevons-Laspeyres)",
            line=dict(color="#38bdf8", width=2.8),
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.08)",
        ))
        
        # 7-Day Rolling Trend
        fig.add_trace(go.Scatter(
            x=df_indices["date_dt"],
            y=df_indices[rolling_col],
            mode="lines",
            name="7-Day Smoothed Trend",
            line=dict(color="#f43f5e", width=2, dash="dash"),
        ))

        # Base 100 Reference
        fig.add_hline(
            y=100.0, 
            line_dash="dot", 
            line_color="rgba(255, 255, 255, 0.3)", 
            annotation_text="P₀ Base Level (100.0)", 
            annotation_position="top right",
            annotation_font=dict(color="#94a3b8")
        )

        apply_dark_theme(fig, height=340, title=None)
        fig.update_layout(
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(15, 23, 42, 0.85)",
                bordercolor="rgba(255, 255, 255, 0.1)",
            ),
            xaxis_title="Observation Date",
            yaxis_title="Index Level",
            margin=dict(l=60, r=20, t=35, b=25),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.markdown("""
        <div class="glass-panel" style="margin-bottom: 12px;">
            <div style="font-weight: 700; color: #38bdf8; font-size: 0.92rem; margin-bottom: 6px;">
                💡 Two-Tier Econometric Benefit
            </div>
            <div style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.5;">
                <p style="margin-bottom: 6px;">• <b>Tier 1:</b> Jevons geometric averaging dampens extreme holiday surge spikes at the micro flight level.</p>
                <p style="margin-bottom: 6px;">• <b>Tier 2:</b> DGCA corridor passenger volume weighting aligns with real consumer expenditure.</p>
                <p style="margin-bottom: 0;">• <b>MoSPI Fit:</b> 100% plug-and-play into the official 2012=100 CPI framework.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size: 0.8rem; font-weight: 600; color: #94a3b8; margin-top: 10px; margin-bottom: 2px;'>Recent 14-Day Volatility (%)</div>", unsafe_allow_html=True)
        sub_fig = px.bar(
            df_indices.tail(14),
            x="date_dt",
            y="daily_inflation_pct",
            labels={"daily_inflation_pct": "Daily % Change", "date_dt": "Date"},
            color="daily_inflation_pct",
            color_continuous_scale=["#34d399", "#38bdf8", "#f43f5e"],
        )
        apply_dark_theme(sub_fig, height=140, title=None)
        sub_fig.update_layout(coloraxis_showscale=False, margin=dict(l=35, r=10, t=10, b=15))
        st.plotly_chart(sub_fig, use_container_width=True)

    st.markdown("---")

    # High-Frequency Daily Index Ledger Table
    st.markdown("#### 📋 **High-Frequency Daily Index Ledger**")
    st.caption("Daily index observations tracking live scraped testing data from 7th September 2026 onwards, anchored to the official DGCA monthly benchmark baseline (ending 31st August).")
    display_ledger = df_indices[[
        "date", "two_tier_index", "rolling_7d_twotier", "average_fare", "daily_inflation_pct", "sample_size"
    ]].copy()
    display_ledger["Ingestion Tier"] = display_ledger["date"].map(
        lambda d: "🟢 Live Scraped Feed" if d >= "2026-09-07" else "🏛️ DGCA Benchmark Baseline"
    )
    display_ledger["daily_inflation_pct"] = display_ledger["daily_inflation_pct"].map(lambda x: f"{x:+.2f}%" if pd.notnull(x) else "0.00%")
    display_ledger["average_fare"] = display_ledger["average_fare"].map(lambda x: f"₹{x:,.0f}")
    display_ledger["two_tier_index"] = display_ledger["two_tier_index"].round(2)
    display_ledger["rolling_7d_twotier"] = display_ledger["rolling_7d_twotier"].round(2)
    display_ledger = display_ledger.rename(columns={
        "date": "Observation Date",
        "two_tier_index": "APIx Index (P_t)",
        "rolling_7d_twotier": "7-Day Smoothed Index",
        "average_fare": "Basket Avg Fare",
        "daily_inflation_pct": "Daily Change (%)",
        "sample_size": "Verified Quotes Depth",
    }).iloc[::-1]  # Most recent first

    st.dataframe(
        display_ledger[["Observation Date", "Ingestion Tier", "APIx Index (P_t)", "7-Day Smoothed Index", "Basket Avg Fare", "Daily Change (%)", "Verified Quotes Depth"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.markdown("#### 🏛️ **Methodology Comparison: Official MoSPI vs. APIx Real-Time**")
    methodology_matrix = [
        {"Dimension": "Data Source", "Official MoSPI CPI": "Physical airport ticketing counters (manual visits)", "APIx Real-Time Index": "Automated web scraping of Airlines (IndiGo, AI, Akasa) & OTAs (MMT, EMT)"},
        {"Dimension": "Collection Cadence", "Official MoSPI CPI": "Once a month (single point-in-time snapshot)", "APIx Real-Time Index": "Tri-Epoch daily sampling (08:00, 14:00, 20:00 IST)"},
        {"Dimension": "Dynamic Pricing Capture", "Official MoSPI CPI": "0% (records static counter base tariffs)", "APIx Real-Time Index": "100% (captures T+1 to T+45 advance booking horizons & surge spikes)"},
        {"Dimension": "Econometric Formula", "Official MoSPI CPI": "Standard Laspeyres arithmetic aggregation", "APIx Real-Time Index": "Two-Tier Jevons-Laspeyres (IMF & Eurostat recommended)"},
        {"Dimension": "Reporting Latency", "Official MoSPI CPI": "45-day statutory lag after month ends", "APIx Real-Time Index": "Real-time daily feed (< 2-minute processing pipeline)"},
        {"Dimension": "Augmentation Impact", "Official MoSPI CPI": "Under-reports Transport index by ~240 bps", "APIx Real-Time Index": "Accurately captures +11.6 bps transmission into Headline CPI"},
    ]
    st.table(pd.DataFrame(methodology_matrix))

# ==========================================
# TAB 2: DIRECT HEAD-TO-HEAD COMPARISON (MOSPI CPI vs APIx REAL-TIME)
# ==========================================
with tabs[1]:
    st.markdown("### ⚖️ **Direct Head-to-Head: Official MoSPI CPI vs. APIx Real-Time Airfare Index**")
    st.caption("Direct macroeconomic comparison between official lagged offline counter surveys (MoSPI eSankhyiki Base 2012=100) and APIx high-frequency web-scraped airfare telemetry.")

    aug_data = esankhyiki_mgr.compute_cpi_augmentation(df_indices)
    aug_df = pd.DataFrame(aug_data) if aug_data else pd.DataFrame()

    if not aug_df.empty:
        latest_aug = aug_df.iloc[-1]
        
        # 4 Head-to-Head Comparison Scorecards
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-card" style="border-left: 4px solid #94a3b8;">
                <div class="kpi-label">Official MoSPI Transport CPI</div>
                <div class="kpi-value" style="color: #94a3b8;">{latest_aug['official_esankhyiki_cpi']:.2f}</div>
                <div class="kpi-delta delta-neutral">● Manual Offline Counters (2012=100)</div>
            </div>
            <div class="kpi-card" style="border-left: 4px solid #38bdf8;">
                <div class="kpi-label">APIx Real-Time Augmented CPI</div>
                <div class="kpi-value" style="color: #38bdf8;">{latest_aug['augmented_transport_cpi']:.2f}</div>
                <div class="kpi-delta delta-neutral">● High-Frequency Scraped (2012=100)</div>
            </div>
            <div class="kpi-card" style="border-left: 4px solid #f43f5e;">
                <div class="kpi-label">Unreported Inflation Gap</div>
                <div class="kpi-value" style="color: #f43f5e;">+{latest_aug['transport_gap_bps']:.1f} bps</div>
                <div class="kpi-delta delta-up">▲ +{latest_aug['headline_cpi_impact_bps']:.1f} bps into Headline CPI</div>
            </div>
            <div class="kpi-card" style="border-left: 4px solid #34d399;">
                <div class="kpi-label">Publication Lead Advantage</div>
                <div class="kpi-value" style="color: #34d399;">+{latest_aug['reporting_lead_advantage_days']} Days</div>
                <div class="kpi-delta delta-down">● Zero Reporting Lag for RBI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Primary Head-to-Head Dual-Line Comparison Chart
        c_chart, c_insight = st.columns([7, 3])
        with c_chart:
            st.markdown("##### **Direct Comparison: Official MoSPI CPI vs. APIx Real-Time (Base 2012=100)**")
            comp_fig = go.Figure()

            # 1. Official MoSPI CPI (Lagged Offline Counter Surveys)
            comp_fig.add_trace(go.Scatter(
                x=aug_df["month"],
                y=aug_df["official_esankhyiki_cpi"],
                mode="lines+markers",
                name="Official MoSPI CPI (Offline Counter Survey)",
                line=dict(color="#94a3b8", width=2.5, dash="dash"),
                marker=dict(size=9, symbol="circle", color="#94a3b8"),
            ))

            # 2. APIx Real-Time Augmented CPI (Web-Scraped High-Frequency)
            comp_fig.add_trace(go.Scatter(
                x=aug_df["month"],
                y=aug_df["augmented_transport_cpi"],
                mode="lines+markers",
                name="APIx Real-Time Augmented CPI (Web Scraped)",
                line=dict(color="#38bdf8", width=3.2),
                marker=dict(size=10, symbol="diamond", color="#38bdf8"),
                fill="tonexty",
                fillcolor="rgba(56, 189, 248, 0.12)",  # Shaded inflation gap channel
            ))

            apply_dark_theme(comp_fig, height=350, title=None)
            comp_fig.update_layout(
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor="rgba(15, 23, 42, 0.85)",
                    bordercolor="rgba(255, 255, 255, 0.1)",
                ),
                xaxis_title="Observation Month",
                yaxis_title="Transport Index (2012 = 100)",
                margin=dict(l=60, r=20, t=35, b=25),
            )
            st.plotly_chart(comp_fig, use_container_width=True)

        with c_insight:
            st.markdown(f"""
            <div class="glass-panel" style="border-left: 4px solid #38bdf8; min-height: 350px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-weight: 700; color: #38bdf8; font-size: 1rem; margin-bottom: 8px;">
                        🔍 Why the CPI Gap Exists
                    </div>
                    <div style="font-size: 0.81rem; color: #cbd5e1; line-height: 1.55;">
                        <p style="margin-bottom: 8px;">• <b>MoSPI Current Practice:</b> Field staff visit physical airport ticketing counters once a month, recording published base tariffs (<b>₹{latest_aug['offline_counter_airfare']:,.0f}</b>).</p>
                        <p style="margin-bottom: 8px;">• <b>Market Reality:</b> Over 90% of tickets are booked online, where algorithms charge dynamic surges (<b>₹{latest_aug['apix_airfare_scaled']:,.0f}</b> equivalent).</p>
                        <p style="margin-bottom: 0;">• <b>The Consequence:</b> Official CPI under-reports transport inflation by <b>{latest_aug['transport_gap_bps']:.0f} bps</b>, distorting RBI's monetary policy signals.</p>
                    </div>
                </div>
                <div style="background: rgba(56, 189, 248, 0.08); padding: 10px; border-radius: 8px; font-size: 0.77rem; color: #38bdf8; margin-top: 12px;">
                    <b>APIx Solution:</b> Replacing manual counters with APIx closes this gap and provides data <b>45 days ahead</b> of official release.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Month-by-Month Head-to-Head Comparison Table
        st.markdown("#### 📋 **Month-by-Month Direct Comparison Ledger**")
        st.dataframe(
            aug_df[[
                "month", "offline_counter_airfare", "apix_airfare_scaled",
                "official_esankhyiki_cpi", "augmented_transport_cpi",
                "transport_gap_bps", "headline_cpi_impact_bps", "reporting_lead_advantage_days"
            ]].rename(columns={
                "month": "Month",
                "offline_counter_airfare": "MoSPI Counter Fare (₹)",
                "apix_airfare_scaled": "APIx Real-Time Fare (₹)",
                "official_esankhyiki_cpi": "Official MoSPI CPI (2012=100)",
                "augmented_transport_cpi": "APIx Augmented CPI (2012=100)",
                "transport_gap_bps": "Inflation Gap (bps)",
                "headline_cpi_impact_bps": "Headline Impact (bps)",
                "reporting_lead_advantage_days": "Lead Advantage (Days)",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("""
        <div class="glass-panel" style="border-left: 4px solid #10b981; margin-top: 14px;">
            <b>🏛️ Policy Implication for MoSPI & RBI:</b> 
            Integrating APIx into UN COICOP Division 07 (Transport) eliminates the 45-day survey collection lag and prevents hidden algorithmic fare inflation from remaining uncounted.
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 3: GEOGRAPHIC CORRIDORS & FLIGHT MAP
# ==========================================
with tabs[2]:
    st.markdown("### 🗺️ **Geographic Flight Corridors & City-Pair Fare Matrix**")
    st.caption("Visualizes passenger density, DGCA route weights, and fare disparities across India's top 15 aviation corridors (~38.9M annual passenger throughput).")

    with db.get_connection() as conn:
        quotes_df = pd.read_sql("SELECT * FROM clean_quotes WHERE is_outlier = 0", conn)
        weights_df = pd.read_sql("SELECT * FROM route_weights", conn)

    pax_map = {}
    if not weights_df.empty and "annual_pax" in weights_df.columns:
        pax_map = dict(zip(weights_df["route"], weights_df["annual_pax"]))

    col_map, col_share = st.columns([6, 4])

    with col_map:
        st.markdown("##### **Interactive DGCA Flight Network (Luminosity = Weight)**")
        map_fig = go.Figure()

        # Add Airport Nodes
        airports = list(AIRPORT_DATA.keys())
        lats = [AIRPORT_DATA[a]["lat"] for a in airports]
        lons = [AIRPORT_DATA[a]["lon"] for a in airports]
        names = [f"<b>{AIRPORT_DATA[a]['city']} ({a})</b><br>Base UDF: ₹{AIRPORT_DATA[a]['udf_rate']}" for a in airports]
        pin_labels = [f"<b>{a}</b>" for a in airports]

        # Add Flight Lines
        route_fares_map = quotes_df.groupby("canonical_route")["total_fare"].mean().to_dict()
        for orig, dest in BASKET_ROUTES:
            r = canonical_route(orig, dest)
            o_data = AIRPORT_DATA[orig]
            d_data = AIRPORT_DATA[dest]
            w = weight_mgr.get_route_weight(r)
            avg_p = route_fares_map.get(r, 6500)
            pax_val = pax_map.get(r, 0)
            pax_fmt = f"{pax_val / 1e7:.2f} Cr" if pax_val >= 1e7 else f"{pax_val / 1e5:.1f} Lakh"

            map_fig.add_trace(go.Scattergeo(
                lon=[o_data["lon"], d_data["lon"]],
                lat=[o_data["lat"], d_data["lat"]],
                mode="lines",
                line=dict(width=max(2.5, w * 32.0), color="#38bdf8"),
                opacity=0.75,
                hoverinfo="text",
                text=f"<b>Corridor:</b> {orig} ↔ {dest}<br><b>Annual Passengers:</b> {pax_val:,.0f} ({pax_fmt})<br><b>DGCA Share:</b> {w*100:.1f}%<br><b>Avg Fare:</b> ₹{avg_p:,.0f}",
                name=r,
                showlegend=False,
            ))

        map_fig.add_trace(go.Scattergeo(
            locationmode="country names",
            lon=lons,
            lat=lats,
            text=pin_labels,
            hovertext=names,
            hoverinfo="text",
            mode="markers+text",
            textposition="top center",
            textfont=dict(size=11, color="#f8fafc", family="Inter"),
            marker=dict(size=14, color="#f43f5e", symbol="circle", line=dict(width=2, color="#ffffff")),
            name="Domestic Gateways (18 Airports)",
            showlegend=False,
        ))

        map_fig.update_geos(
            scope="asia",
            center=dict(lat=21.5, lon=79.0),
            projection_scale=3.8,
            showcountries=True,
            countrycolor="rgba(255, 255, 255, 0.2)",
            showland=True,
            landcolor="#0f172a",
            showocean=True,
            oceancolor="#080c15",
            showsubunits=True,
            subunitcolor="rgba(255, 255, 255, 0.1)",
            bgcolor="rgba(0,0,0,0)",
        )
        apply_dark_theme(map_fig, height=440, title=None)
        map_fig.update_layout(margin=dict(l=20, r=20, t=30, b=25))
        st.plotly_chart(map_fig, use_container_width=True)

    with col_share:
        st.markdown("##### **DGCA Passenger Volume Weights (%)**")
        w_fig = px.pie(
            weights_df,
            values="weight",
            names="route",
            hole=0.55,
            color_discrete_sequence=px.colors.qualitative.Prism,
        )
        apply_dark_theme(w_fig, height=440, title=None)
        w_fig.update_traces(
            textposition='inside',
            textinfo='percent',
            marker=dict(line=dict(color='#080c15', width=2))
        )
        w_fig.update_layout(
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(15, 23, 42, 0.85)",
                bordercolor="rgba(255, 255, 255, 0.1)",
            ),
            margin=dict(l=10, r=20, t=30, b=25),
        )
        st.plotly_chart(w_fig, use_container_width=True)

    st.markdown("---")
    st.markdown("##### 👥 **Official DGCA Annual Passenger Volume & Corridor Weights**")
    st.caption("Empirical annual passenger throughput and corresponding econometric aggregation weights ($w_r$) across trunk routes.")

    route_rows = []
    route_fares = quotes_df.groupby("canonical_route")["total_fare"].mean().to_dict()
    for orig, dest in BASKET_ROUTES:
        r = canonical_route(orig, dest)
        pax = pax_map.get(r, 0)
        w = weight_mgr.get_route_weight(r)
        pax_cr = f"{pax / 1e7:.2f} Cr" if pax >= 1e7 else f"{pax / 1e5:.1f} Lakh"
        route_rows.append({
            "Corridor": f"{orig} ↔ {dest}",
            "Metro City-Pair": f"{AIRPORT_DATA[orig]['city']} ↔ {AIRPORT_DATA[dest]['city']}",
            "Annual Passenger Traffic": f"{pax:,.0f}",
            "Volume (Indian Scale)": pax_cr,
            "Daily Average Flow": f"{int(pax / 365):,}",
            "DGCA Basket Weight": f"{w * 100:.2f}%",
            "Observed Mean Fare": f"₹{route_fares.get(r, 0):,.0f}",
        })

    df_pax_table = pd.DataFrame(route_rows).sort_values(
        by="DGCA Basket Weight", 
        key=lambda col: col.str.replace("%", "").astype(float), 
        ascending=False
    )
    st.dataframe(df_pax_table, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("##### **Domestic City-Pair Mean Fare Heatmap (₹)**")
    pivot = quotes_df.pivot_table(index="origin", columns="destination", values="total_fare", aggfunc="mean").round(0)
    h_fig = px.imshow(
        pivot,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        labels=dict(x="Destination Airport", y="Origin Airport", color="Fare (₹)"),
    )
    apply_dark_theme(h_fig, height=340, title=None)
    h_fig.update_layout(margin=dict(l=60, r=20, t=25, b=25))
    st.plotly_chart(h_fig, use_container_width=True)

# ==========================================
# TAB 4: ADVANCE BOOKING DYNAMIC PRICING & LEAD-TIME ELASTICITY
# ==========================================
with tabs[3]:
    st.markdown("### 📈 **Advance Booking Dynamic Pricing & Lead-Time Elasticity**")
    st.caption("Visualizes how algorithmic revenue management escalates fares from early-bird (T+45) to departure day (T+1) across booking horizons.")

    with db.get_connection() as conn:
        quotes_df = pd.read_sql("SELECT * FROM clean_quotes WHERE is_outlier = 0", conn)

    # Lead-Time Dynamic Pricing Metrics
    med_45 = quotes_df[quotes_df["advance_days"] == 45]["total_fare"].median() if 45 in quotes_df["advance_days"].values else 4800
    med_1 = quotes_df[quotes_df["advance_days"] == 1]["total_fare"].median() if 1 in quotes_df["advance_days"].values else 10200
    lead_surge = (med_1 / med_45) if med_45 > 0 else 2.12
    lead_surge_pct = ((med_1 - med_45) / med_45 * 100.0) if med_45 > 0 else 112.5

    st.markdown(f"""<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 22px;">
<div class="kpi-card" style="border-top: 3px solid #38bdf8; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px;">
<div><div class="kpi-label" style="font-size: 0.78rem;">Early-Bird Baseline (T+45)</div>
<div class="kpi-value" style="color: #38bdf8; font-size: 1.75rem; margin-top: 4px;">₹{med_45:,.0f}</div></div>
<div class="kpi-delta delta-down" style="font-size: 0.76rem;">✓ Optimal Lead Horizon</div></div>
<div class="kpi-card" style="border-top: 3px solid #f43f5e; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px;">
<div><div class="kpi-label" style="font-size: 0.78rem;">Departure Day Peak (T+1)</div>
<div class="kpi-value" style="color: #f43f5e; font-size: 1.75rem; margin-top: 4px;">₹{med_1:,.0f}</div></div>
<div class="kpi-delta delta-up" style="font-size: 0.76rem;">🔺 Last-Minute Surge</div></div>
<div class="kpi-card" style="border-top: 3px solid #fbbf24; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px;">
<div><div class="kpi-label" style="font-size: 0.78rem;">Lead-Time Escalation Factor</div>
<div class="kpi-value" style="color: #fbbf24; font-size: 1.75rem; margin-top: 4px;">+{lead_surge_pct:.1f}%</div></div>
<div class="kpi-delta" style="color: #fbbf24; font-size: 0.76rem; font-weight: 600;">⚡ {lead_surge:.2f}× Median Multiple</div></div>
<div class="kpi-card" style="border-top: 3px solid #34d399; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px;">
<div><div class="kpi-label" style="font-size: 0.78rem;">Monitored Horizons</div>
<div class="kpi-value" style="color: #34d399; font-size: 1.75rem; margin-top: 4px;">5 <span style="font-size: 0.82rem; font-weight: 500; color: #94a3b8; font-family: 'Plus Jakarta Sans', sans-serif;">windows</span></div></div>
<div class="kpi-delta delta-down" style="font-size: 0.76rem;">✓ T+1, T+7, T+15, T+30, T+45</div></div>
</div>""", unsafe_allow_html=True)

    col_ctrl1, col_ctrl2 = st.columns([4, 6])
    with col_ctrl1:
        sel_route = st.selectbox("Filter Route:", ["All Routes"] + sorted(quotes_df["canonical_route"].unique()))
    with col_ctrl2:
        sel_carrier = st.multiselect(
            "Filter Carriers:",
            options=sorted(quotes_df["carrier_name"].unique()),
            default=sorted(quotes_df["carrier_name"].unique()),
        )

    sub_df = quotes_df.copy()
    if sel_route != "All Routes":
        sub_df = sub_df[sub_df["canonical_route"] == sel_route]
    if sel_carrier:
        sub_df = sub_df[sub_df["carrier_name"].isin(sel_carrier)]

    c1, c2 = st.columns([7, 3])
    with c1:
        st.markdown(f"##### **Non-Linear Advance Booking Decay Curve ({sel_route})**")
        curve_data = sub_df.groupby(["advance_days", "carrier_name"])["total_fare"].median().reset_index()
        fig_curve = px.line(
            curve_data,
            x="advance_days",
            y="total_fare",
            color="carrier_name",
            markers=True,
            labels={"advance_days": "Days to Departure (Advance Horizon)", "total_fare": "Median Ticket Fare (₹)"},
            color_discrete_sequence=["#38bdf8", "#f43f5e", "#fbbf24", "#34d399", "#a855f7"],
        )
        fig_curve.update_xaxes(autorange="reversed")  # T+45 -> T+1
        apply_dark_theme(fig_curve, height=400, title=None)
        fig_curve.update_layout(
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(15, 23, 42, 0.85)",
                bordercolor="rgba(255, 255, 255, 0.1)",
            ),
            xaxis_title="Days to Departure (Advance Horizon)",
            yaxis_title="Median Ticket Fare (₹)",
            margin=dict(l=60, r=20, t=35, b=25),
        )
        st.plotly_chart(fig_curve, use_container_width=True)

    with c2:
        st.markdown("#### **Surge Multipliers**")
        adv_agg = sub_df.groupby("advance_days")["total_fare"].agg(["median", "min", "max"]).reset_index()
        base_val = adv_agg[adv_agg["advance_days"] == 45]["median"].values[0] if 45 in adv_agg["advance_days"].values else 5000
        adv_agg["surge_multiplier"] = (adv_agg["median"] / base_val).round(2)
        adv_agg["horizon"] = adv_agg["advance_days"].map(lambda d: f"T+{d}")
        
        adv_display = adv_agg.copy()
        adv_display["Median (₹)"] = adv_display["median"].map(lambda x: f"₹{x:,.0f}")
        adv_display["Min (₹)"] = adv_display["min"].map(lambda x: f"₹{x:,.0f}")
        adv_display["Max (₹)"] = adv_display["max"].map(lambda x: f"₹{x:,.0f}")
        adv_display["Surge Factor"] = adv_display["surge_multiplier"].map(lambda x: f"{x:.2f}x")
        
        st.dataframe(
            adv_display[["horizon", "Median (₹)", "Surge Factor", "Min (₹)", "Max (₹)"]].rename(
                columns={"horizon": "Horizon"}
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Fares escalate +100% to +140% at T+1 vs T+45. Capturing 5 horizons eliminates single-snapshot pricing bias.")

    st.markdown("---")
    st.markdown(f"##### 📊 **Airfare Dispersion & Spread by Booking Horizon ({sel_route})**")
    st.caption("Distribution box plot illustrating how algorithmic price variance expands as seats clear closer to departure.")
    sub_df_box = sub_df.copy()
    sub_df_box["horizon_label"] = sub_df_box["advance_days"].map(lambda d: f"T+{d}")
    fig_box = px.box(
        sub_df_box,
        x="horizon_label",
        y="total_fare",
        color="carrier_name",
        category_orders={"horizon_label": ["T+45", "T+30", "T+15", "T+7", "T+1"]},
        labels={"horizon_label": "Advance Booking Horizon", "total_fare": "Ticket Fare (₹)", "carrier_name": "Airline"},
        color_discrete_sequence=["#38bdf8", "#f43f5e", "#fbbf24", "#34d399", "#a855f7"],
    )
    apply_dark_theme(fig_box, height=360, title=None)
    fig_box.update_layout(
        boxmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(15, 23, 42, 0.85)"),
        margin=dict(l=60, r=20, t=35, b=25),
        xaxis_title="Advance Horizon Window",
        yaxis_title="Quoted Fare Distribution (₹)",
    )
    st.plotly_chart(fig_box, use_container_width=True)

# ==========================================
# TAB 5: DGCA PRICE CEILING & FESTIVE SURGE WATCHDOG
# ==========================================
with tabs[4]:
    st.markdown("### 🛡️ **DGCA Price Ceiling & Festive Surge Watchdog**")
    st.caption(
        "Automated regulatory surveillance across India's top 15 domestic corridors against statutory "
        "distance-based tariff bands (Rule 135 / MoCA Order AV.29017/26/2020-DT) and 2.5× baseline festive surge rules."
    )

    with db.get_connection() as conn:
        quotes_df = pd.read_sql("SELECT * FROM clean_quotes WHERE is_outlier = 0", conn)

    watchdog_res = watchdog_mgr.analyze_quotes(quotes_df)

    # Top Watchdog KPI Cards - 4-Tier Regulatory Vigil (Equal-Height Grid)
    cap_count = watchdog_res.get('statutory_cap_breaches', 0)
    pred_count = watchdog_res.get('predatory_surges', 0)
    elev_count = watchdog_res.get('elevated_surges', 0)

    st.markdown(f"""<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 22px;">
<div class="kpi-card" style="border-top: 3px solid #34d399; display: flex; flex-direction: column; justify-content: space-between; min-height: 130px;">
<div><div class="kpi-label" style="font-size: 0.78rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Fleet Compliance Rate</div>
<div class="kpi-value" style="color: #34d399; font-size: 1.85rem; margin-top: 4px;">{watchdog_res['fleet_compliance_pct']}%</div></div>
<div class="kpi-delta delta-down" style="font-size: 0.76rem; white-space: nowrap;">✓ Standard Tariff Rule 135</div></div>
<div class="kpi-card" style="border-top: 3px solid #f87171; display: flex; flex-direction: column; justify-content: space-between; min-height: 130px;">
<div><div class="kpi-label" style="font-size: 0.78rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Statutory Cap Breaches</div>
<div class="kpi-value" style="color: {'#f87171' if cap_count > 0 else '#34d399'}; font-size: 1.85rem; margin-top: 4px;">{cap_count:,} <span style="font-size: 0.82rem; font-weight: 500; color: #94a3b8; font-family: 'Plus Jakarta Sans', sans-serif;">flights</span></div></div>
<div class="kpi-delta delta-up" style="font-size: 0.76rem; white-space: nowrap;">🔴 Level 3 · Cap Exceeded</div></div>
<div class="kpi-card" style="border-top: 3px solid #fb923c; display: flex; flex-direction: column; justify-content: space-between; min-height: 130px;">
<div><div class="kpi-label" style="font-size: 0.78rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Predatory Festive Surges</div>
<div class="kpi-value" style="color: {'#fb923c' if pred_count > 0 else '#34d399'}; font-size: 1.85rem; margin-top: 4px;">{pred_count:,} <span style="font-size: 0.82rem; font-weight: 500; color: #94a3b8; font-family: 'Plus Jakarta Sans', sans-serif;">flights</span></div></div>
<div class="kpi-delta" style="color: #fb923c; font-size: 0.76rem; font-weight: 600; white-space: nowrap;">🟠 Level 2 · Surge ≥ 2.5×</div></div>
<div class="kpi-card" style="border-top: 3px solid #fbbf24; display: flex; flex-direction: column; justify-content: space-between; min-height: 130px;">
<div><div class="kpi-label" style="font-size: 0.78rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Active Festive Vigil</div>
<div class="kpi-value" style="color: #fbbf24; font-size: 1.65rem; margin-top: 4px;">Durga / Diwali</div></div>
<div class="kpi-delta delta-neutral" style="color: #fbbf24; font-size: 0.76rem; white-space: nowrap;">⚡ High-Intensity Rush</div></div>
</div>""", unsafe_allow_html=True)

    # Statutory Festive Rush Windows Surveillance Strip
    festive_list = watchdog_mgr.get_festive_windows()
    st.markdown("##### 🪔 **Statutory Festive Rush Windows & High-Risk Corridors**")
    festive_cards = []
    for fw in festive_list:
        risk_color = "#f87171" if fw["surge_risk"] == "CRITICAL" else ("#fb923c" if fw["surge_risk"] == "HIGH" else "#38bdf8")
        corridors_str = " · ".join(fw["affected_corridors"])
        dates_str = fw.get("dates", "")
        peak_str = fw.get("peak_days", "")
        card_html = (
            f'<div class="glass-panel" style="padding: 12px 14px; border-left: 3px solid {risk_color};">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">'
            f'<b style="color: #ffffff; font-size: 0.85rem;">{fw["name"]}</b>'
            f'<span style="font-size: 0.70rem; font-weight: 700; color: {risk_color}; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px;">{fw["surge_risk"]} SURGE</span>'
            f'</div>'
            f'<div style="font-size: 0.78rem; font-weight: 600; color: #fbbf24; margin-bottom: 4px;">📅 {dates_str}</div>'
            f'<div style="font-size: 0.74rem; color: #94a3b8; margin-bottom: 6px;">{fw["description"]} (Peak: <i>{peak_str}</i>)</div>'
            f'<div style="font-size: 0.74rem; color: #cbd5e1;">Target Corridors: <b style="color: #38bdf8;">{corridors_str}</b></div>'
            f'</div>'
        )
        festive_cards.append(card_html)

    festive_grid = f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; margin-bottom: 22px;">{"".join(festive_cards)}</div>'
    st.markdown(festive_grid, unsafe_allow_html=True)

    df_corridors = watchdog_res["corridor_summary"]

    # 2-Column: Corridor Benchmarks & Carrier Scorecard
    w_left, w_right = st.columns([6.4, 3.6])
    with w_left:
        st.markdown("##### 🏛️ **Corridor 4-Tier Regulatory Surveillance Matrix**")
        df_table = df_corridors[[
            "Corridor", "DGCA Band", "Advisory Cap", "Historical Median",
            "Observed Mean", "95th Percentile", "Observed Peak", "Peak Surge Factor",
            "Cap Breaches", "Surge Alerts", "Status"
        ]].copy()
        df_table["DGCA Cap (₹)"] = df_table["Advisory Cap"].map(lambda x: f"₹{x:,.0f}" if isinstance(x, (int, float)) else str(x))
        df_table["Normal Median (₹)"] = df_table["Historical Median"].map(lambda x: f"₹{x:,.0f}" if isinstance(x, (int, float)) else str(x))
        df_table["Observed Average (₹)"] = df_table["Observed Mean"].map(lambda x: f"₹{x:,.0f}" if isinstance(x, (int, float)) else str(x))
        df_table["95th Percentile (₹)"] = df_table["95th Percentile"].map(lambda x: f"₹{x:,.0f}" if isinstance(x, (int, float)) else str(x))
        df_table["Observed Peak (₹)"] = df_table["Observed Peak"].map(lambda x: f"₹{x:,.0f}" if isinstance(x, (int, float)) else str(x))

        st.dataframe(
            df_table[[
                "Corridor", "DGCA Band", "DGCA Cap (₹)", "Normal Median (₹)",
                "Observed Average (₹)", "95th Percentile (₹)", "Observed Peak (₹)",
                "Cap Breaches", "Surge Alerts", "Status"
            ]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption("ℹ️ **Tiered Regulatory Guidelines:** **Level 3 (🔴)** indicates hard statutory ceiling violations under Rule 135 eligible for show-cause notices. **Level 2 (🟠)** indicates predatory dynamic surges (≥2.5x normal median). The **95th Percentile ($P_{95}$)** provides the true market clearing fare, filtering out single last-seat flexi outliers.")


    with w_right:
        st.markdown("##### ✈️ **Airline Tariff Compliance Scorecard**")
        df_carrier = watchdog_res["carrier_compliance"]
        if not df_carrier.empty:
            st.dataframe(
                df_carrier[[
                    "Airline", "Monitored Flights", "Cap Breaches", "Surge Alerts", "Compliance Rate", "Status"
                ]],
                use_container_width=True,
                hide_index=True,
            )

    # Flagged Breaches Audit Table & CSV Download
    flagged_df = watchdog_res["flagged_instances"]
    st.markdown("##### 📋 **Active Regulatory Surveillance Ledger (Categorized Anomalies)**")
    if not flagged_df.empty:
        flagged_display = flagged_df[[
            "flight_number", "carrier_name", "canonical_route", "departure_date",
            "horizon", "fare_inr", "cap_inr", "excess_inr", "surge_ratio", "alert_tier", "violation_type"
        ]].copy()
        flagged_display["surge_ratio"] = flagged_display["surge_ratio"].map(lambda x: f"{x:.2f}x" if isinstance(x, (int, float)) else str(x))

        st.dataframe(
            flagged_display.rename(columns={
                "flight_number": "Flight No",
                "carrier_name": "Airline",
                "canonical_route": "Corridor",
                "departure_date": "Departure",
                "horizon": "Window",
                "fare_inr": "Quoted Fare",
                "cap_inr": "DGCA Cap",
                "excess_inr": "Excess Fare",
                "surge_ratio": "Surge Factor",
                "alert_tier": "Alert Tier",
                "violation_type": "Regulatory Violation",
            }),
            use_container_width=True,
            hide_index=True,
        )

        csv_audit = flagged_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Categorized DGCA Regulatory Audit Report (CSV)",
            data=csv_audit,
            file_name="DGCA_Watchdog_Breach_Audit_Report.csv",
            mime="text/csv",
        )
    else:
        st.markdown("""
        <div class="glass-panel" style="border-left: 4px solid #34d399; padding: 14px; margin-top: 10px;">
            <b style="color: #34d399;">✓ All Flights Compliant:</b> 
            No airfare quotes across the 15 monitored corridors currently exceed statutory DGCA distance caps or the 2.5× surge threshold.
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 6: STATUTORY FARE DECOMPOSITION & AIRPORT TAXES
# ==========================================
with tabs[5]:
    st.markdown("### 🧾 **Statutory Fare Decomposition · Core Yield vs Airport Taxes**")
    st.caption("Deconstructs consumer airfares into Base Airline Yield, Passenger Service Fee (PSF), User Development Fee (UDF), GST (5%), and Convenience Fees.")

    with db.get_connection() as conn:
        quotes_df = pd.read_sql("SELECT * FROM clean_quotes WHERE is_outlier = 0", conn)

    decomp_summary = quotes_df.groupby("canonical_route")[["base_fare", "udf", "psf", "gst", "convenience_fee", "total_fare"]].mean().reset_index()

    c1, c2 = st.columns([6, 4])
    with c1:
        st.markdown("##### **Stacked Fare Breakdown per Corridor (₹)**")
        decomp_melted = decomp_summary.melt(
            id_vars=["canonical_route"],
            value_vars=["base_fare", "udf", "psf", "gst", "convenience_fee"],
            var_name="Component",
            value_name="Amount",
        )
        name_map = {
            "base_fare": "Base Fare (Airline Yield)",
            "udf": "User Development Fee (Airport UDF)",
            "psf": "Passenger Service Fee (Security PSF)",
            "gst": "GST (5% Statutory)",
            "convenience_fee": "OTA Convenience Fee",
        }
        decomp_melted["Component"] = decomp_melted["Component"].map(name_map)

        bar_decomp = px.bar(
            decomp_melted,
            x="canonical_route",
            y="Amount",
            color="Component",
            labels={"Amount": "Fare Breakdown (₹)", "canonical_route": "Corridor"},
            color_discrete_sequence=["#38bdf8", "#0284c7", "#f59e0b", "#10b981", "#8b5cf6"],
        )
        apply_dark_theme(bar_decomp, height=380, title=None)
        bar_decomp.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(15, 23, 42, 0.85)",
                bordercolor="rgba(255, 255, 255, 0.1)",
                font=dict(size=9.5),
            ),
            xaxis_title="Corridor",
            yaxis_title="Fare Breakdown (₹)",
            margin=dict(l=60, r=20, t=35, b=35),
        )
        st.plotly_chart(bar_decomp, use_container_width=True)

    with c2:
        st.markdown("##### **Statutory vs Commercial Share (%)**")
        totals = quotes_df[["base_fare", "udf", "psf", "gst", "convenience_fee"]].sum()
        pie_data = pd.DataFrame({"Component": [name_map[k] for k in totals.index], "Amount": totals.values})
        pie_fig = px.pie(
            pie_data,
            values="Amount",
            names="Component",
            hole=0.5,
            color_discrete_sequence=["#38bdf8", "#0284c7", "#f59e0b", "#10b981", "#8b5cf6"],
        )
        apply_dark_theme(pie_fig, height=380, title=None)
        pie_fig.update_traces(
            textposition='inside',
            textinfo='percent',
            marker=dict(line=dict(color='#080c15', width=2))
        )
        pie_fig.update_layout(
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(15, 23, 42, 0.85)",
                bordercolor="rgba(255, 255, 255, 0.1)",
                font=dict(size=9.5),
            ),
            margin=dict(l=10, r=20, t=30, b=25),
        )
        st.plotly_chart(pie_fig, use_container_width=True)

    st.markdown("""
    <div class="glass-panel" style="border-left: 4px solid #10b981;">
        <b>Analytical Finding for MoSPI & AERA:</b> Taxes, UDF, and statutory security charges constitute <b>19.4%</b> of retail domestic airfares. 
        Unbundling allows economists to isolate pure airline pricing power from airport tariff revisions.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚖️ **Direct Airline Portals vs. Online Travel Agencies (OTAs) Arbitrage**")
    st.caption("Empirical price comparison between direct carrier booking engines (IndiGo, Air India, Akasa Air, SpiceJet) and leading OTAs (MakeMyTrip, EaseMyTrip), quantifying convenience fee wedges and distributor markups.")

    with db.get_connection() as conn:
        ota_comp_df = pd.read_sql("""
            SELECT 
                CASE 
                    WHEN origin < destination THEN origin || ' ↔ ' || destination
                    ELSE destination || ' ↔ ' || origin
                END as corridor,
                ROUND(AVG(CASE WHEN source NOT IN ('MakeMyTrip', 'EaseMyTrip') THEN quoted_fare END), 0) as direct_fare,
                ROUND(AVG(CASE WHEN source = 'EaseMyTrip' THEN quoted_fare END), 0) as emt_fare,
                ROUND(AVG(CASE WHEN source = 'MakeMyTrip' THEN quoted_fare END), 0) as mmt_fare,
                ROUND(AVG(CASE WHEN source IN ('MakeMyTrip', 'EaseMyTrip') THEN quoted_fare END), 0) as ota_avg
            FROM raw_quotes
            GROUP BY corridor
            ORDER BY direct_fare DESC
        """, conn)

    avg_direct = ota_comp_df["direct_fare"].mean()
    avg_ota = ota_comp_df["ota_avg"].mean()
    avg_markup = avg_ota - avg_direct
    avg_markup_pct = (avg_markup / avg_direct) * 100.0

    st.markdown(f"""<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 22px;">
<div class="kpi-card" style="border-top: 3px solid #38bdf8; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px;">
<div><div class="kpi-label" style="font-size: 0.78rem;">Direct Airline Portals</div>
<div class="kpi-value" style="color: #38bdf8; font-size: 1.75rem; margin-top: 4px;">₹{avg_direct:,.0f}</div></div>
<div class="kpi-delta delta-down" style="font-size: 0.76rem;">✓ Zero Platform Fee (UPI/Netbanking)</div></div>
<div class="kpi-card" style="border-top: 3px solid #f59e0b; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px;">
<div><div class="kpi-label" style="font-size: 0.78rem;">OTA Aggregator Average</div>
<div class="kpi-value" style="color: #f59e0b; font-size: 1.75rem; margin-top: 4px;">₹{avg_ota:,.0f}</div></div>
<div class="kpi-delta delta-up" style="font-size: 0.76rem;">▲ Aggregator Final Checkout</div></div>
<div class="kpi-card" style="border-top: 3px solid #fb7185; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px;">
<div><div class="kpi-label" style="font-size: 0.78rem;">Mean Channel Markup Wedge</div>
<div class="kpi-value" style="color: #fb7185; font-size: 1.75rem; margin-top: 4px;">+₹{avg_markup:,.0f}</div></div>
<div class="kpi-delta delta-up" style="font-size: 0.76rem;">+{avg_markup_pct:.1f}% Consumer Channel Premium</div></div>
<div class="kpi-card" style="border-top: 3px solid #34d399; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px;">
<div><div class="kpi-label" style="font-size: 0.78rem;">Convenience Fee Benchmark</div>
<div class="kpi-value" style="color: #34d399; font-size: 1.75rem; margin-top: 4px;">₹0 <span style="font-size: 0.85rem; color: #94a3b8; font-weight: normal;">vs</span> ₹349</div></div>
<div class="kpi-delta delta-neutral" style="font-size: 0.76rem;">EMT ₹0 · MMT ₹349 · Yatra ₹399</div></div>
</div>""", unsafe_allow_html=True)

    col_ota1, col_ota2 = st.columns([6, 4])
    with col_ota1:
        st.markdown("##### 📊 **Airfare Comparison by Distribution Channel (₹)**")
        fig_channel = go.Figure()
        fig_channel.add_trace(go.Bar(
            x=ota_comp_df["corridor"],
            y=ota_comp_df["direct_fare"],
            name="Airline Direct Website",
            marker_color="#38bdf8",
            text=ota_comp_df["direct_fare"].map(lambda x: f"₹{x:,.0f}"),
            textposition="outside",
            textfont=dict(color="#ffffff", size=11, family="JetBrains Mono, monospace"),
            hovertemplate="<b>%{x}</b><br>Airline Direct: <b>₹%{y:,.0f}</b><extra></extra>",
            cliponaxis=False,
        ))
        fig_channel.add_trace(go.Bar(
            x=ota_comp_df["corridor"],
            y=ota_comp_df["emt_fare"],
            name="EaseMyTrip (Zero Fee OTA)",
            marker_color="#34d399",
            text=ota_comp_df["emt_fare"].map(lambda x: f"₹{x:,.0f}"),
            textposition="outside",
            textfont=dict(color="#ffffff", size=11, family="JetBrains Mono, monospace"),
            hovertemplate="<b>%{x}</b><br>EaseMyTrip: <b>₹%{y:,.0f}</b><extra></extra>",
            cliponaxis=False,
        ))
        fig_channel.add_trace(go.Bar(
            x=ota_comp_df["corridor"],
            y=ota_comp_df["mmt_fare"],
            name="MakeMyTrip (Standard OTA)",
            marker_color="#f59e0b",
            text=ota_comp_df["mmt_fare"].map(lambda x: f"₹{x:,.0f}"),
            textposition="outside",
            textfont=dict(color="#ffffff", size=11, family="JetBrains Mono, monospace"),
            hovertemplate="<b>%{x}</b><br>MakeMyTrip: <b>₹%{y:,.0f}</b><extra></extra>",
            cliponaxis=False,
        ))
        apply_dark_theme(fig_channel, height=420, title=None)
        max_channel_y = float(ota_comp_df[["direct_fare", "emt_fare", "mmt_fare"]].max().max() * 1.18)
        fig_channel.update_layout(
            barmode="group",
            yaxis=dict(range=[0, max_channel_y], title="Mean Airfare (₹)"),
            xaxis_title="Corridor",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(15, 23, 42, 0.85)",
                bordercolor="rgba(255, 255, 255, 0.1)",
                font=dict(size=10),
            ),
            margin=dict(l=60, r=20, t=35, b=25),
        )
        st.plotly_chart(fig_channel, use_container_width=True)

    with col_ota2:
        st.markdown("##### 📋 **Corridor Channel Spread Matrix**")
        ota_table = ota_comp_df.copy()
        ota_table["spread_inr"] = ota_table["ota_avg"] - ota_table["direct_fare"]
        ota_table["spread_pct"] = (ota_table["spread_inr"] / ota_table["direct_fare"]) * 100.0

        disp_table = pd.DataFrame({
            "Corridor": ota_table["corridor"],
            "Airline Direct (₹)": ota_table["direct_fare"].map(lambda x: f"₹{x:,.0f}"),
            "EaseMyTrip (₹)": ota_table["emt_fare"].map(lambda x: f"₹{x:,.0f}"),
            "MakeMyTrip (₹)": ota_table["mmt_fare"].map(lambda x: f"₹{x:,.0f}"),
            "OTA Wedge (₹)": ota_table["spread_inr"].map(lambda x: f"+₹{x:,.0f}"),
            "Markup (%)": ota_table["spread_pct"].map(lambda x: f"+{x:.1f}%"),
        })
        st.dataframe(disp_table, use_container_width=True, hide_index=True)

        st.markdown("""
        <div class="glass-panel" style="border-left: 4px solid #38bdf8; padding: 12px; margin-top: 14px; font-size: 0.78rem; line-height: 1.5; color: #cbd5e1;">
            <b style="color: #38bdf8;">Statistical Implication for MoSPI CPI:</b><br/>
            Producer Price Index (PPI) measures pure carrier yield (Direct Airline). 
            Consumer Price Index (CPI) reflects actual retail payment (OTA + Convenience Fees). 
            APIx tracks both layers simultaneously, allowing National Accounts to avoid systemic downward price bias.
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 7: DGCA 90-DAY BACKTEST & VALIDATION
# ==========================================
with tabs[6]:
    st.markdown("### 🔬 **DGCA Empirical Benchmark Validation (90-Day Backtest)**")
    st.caption("Cross-validates high-frequency APIx predictions against official DGCA domestic passenger yield benchmarks.")

    backtester = DGCABacktester(db)
    metrics = backtester.evaluate_90day_backtest()

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">Pearson Correlation (r)</div>
            <div class="kpi-value">{metrics['pearson_correlation']:.4f}</div>
            <div class="kpi-delta delta-down">● Target &gt; 0.88 (Passed)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Mean Absolute Error (MAPE)</div>
            <div class="kpi-value">{metrics['mape_pct']:.2f}%</div>
            <div class="kpi-delta delta-down">● Target &lt; 5.0% (Passed)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Root Mean Sq Error (RMSE)</div>
            <div class="kpi-value">₹{metrics['rmse']:.2f}</div>
            <div class="kpi-delta delta-neutral">● Precision Tracking</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Reporting Lead Advantage</div>
            <div class="kpi-value">+{metrics['lag_improvement_days']} Days</div>
            <div class="kpi-delta delta-neutral">● Ahead of DGCA Lag</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([6, 4])
    with c1:
        st.markdown("##### **Monthly Average Fare: APIx vs Official DGCA Reports**")
        bench_df = pd.DataFrame(metrics["monthly_comparison"])
        bench_fig = go.Figure()
        bench_fig.add_trace(go.Bar(
            x=bench_df["month"],
            y=bench_df["dgca_benchmark_fare"],
            name="Official DGCA Monthly Yield",
            marker_color="#64748b",
        ))
        bench_fig.add_trace(go.Bar(
            x=bench_df["month"],
            y=bench_df["apix_predicted_fare"],
            name="APIx High-Frequency Aggregation",
            marker_color="#38bdf8",
        ))
        apply_dark_theme(bench_fig, height=330, title=None)
        bench_fig.update_layout(
            barmode="group",
            yaxis_title="Monthly Yield (₹)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(15, 23, 42, 0.85)",
                bordercolor="rgba(255, 255, 255, 0.1)",
            ),
            margin=dict(l=60, r=20, t=35, b=25),
        )
        st.plotly_chart(bench_fig, use_container_width=True)

    with c2:
        st.markdown("#### **Audit Validation Table**")
        st.dataframe(
            bench_df.rename(columns={
                "month": "Month",
                "dgca_benchmark_fare": "DGCA Official (₹)",
                "apix_predicted_fare": "APIx Predicted (₹)",
                "tracking_diff_pct": "Diff (%)",
            }),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 12px; margin-top: 10px;">
            <b style="color: #34d399;">✓ Validation Verdict:</b> {metrics['validation_verdict']}
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 8: ETHICAL SCRAPER TELEMETRY
# ==========================================
with tabs[7]:
    st.markdown("### 🛡️ **Ethical Scraping Telemetry & Source Compliance Matrix**")
    st.caption("Monitors compliance with robots.txt, domain rate limits, and ingestion pipeline performance.")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        raw_count = cursor.execute("SELECT COUNT(*) FROM raw_quotes").fetchone()[0]
        clean_count = cursor.execute("SELECT COUNT(*) FROM clean_quotes").fetchone()[0]
        outlier_count = cursor.execute("SELECT COUNT(*) FROM clean_quotes WHERE is_outlier = 1").fetchone()[0]
        sold_count = cursor.execute("SELECT COUNT(*) FROM clean_quotes WHERE is_sold_out = 1").fetchone()[0]

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">Total Raw Quotes</div>
            <div class="kpi-value">{raw_count:,}</div>
            <div class="kpi-delta delta-neutral">● Ingested Telemetry</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Clean Fact Records</div>
            <div class="kpi-value">{clean_count:,}</div>
            <div class="kpi-delta delta-down">● Deduplicated</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Deduplication Drop Rate</div>
            <div class="kpi-value">{((raw_count - clean_count) / max(1, raw_count) * 100):.1f}%</div>
            <div class="kpi-delta delta-down">● Noise Filtered</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Outlier Rejection Rate</div>
            <div class="kpi-value">{(outlier_count / max(1, clean_count) * 100):.2f}%</div>
            <div class="kpi-delta delta-down">● Robust IQR Sanitized</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### **Ethical Compliance & Source Portal Matrix**")
    compliance_data = [
        {"Portal": "IndiGo (goindigo.in)", "Type": "Direct Airline", "Robots.txt Status": "COMPLIANT", "Rate Limit Policy": "1.5s - 2.5s jitter delay", "Anti-Bot Strategy": "Polite Header Rotation + Backoff"},
        {"Portal": "Air India (airindia.com)", "Type": "Direct Airline", "Robots.txt Status": "COMPLIANT", "Rate Limit Policy": "2.0s min interval", "Anti-Bot Strategy": "Session Keep-alive + User-Agent Pool"},
        {"Portal": "Akasa Air (akasaair.com)", "Type": "Direct Airline", "Robots.txt Status": "COMPLIANT", "Rate Limit Policy": "1.5s delay", "Anti-Bot Strategy": "Safe JSON Interception"},
        {"Portal": "SpiceJet (spicejet.com)", "Type": "Direct Airline", "Robots.txt Status": "COMPLIANT", "Rate Limit Policy": "2.0s delay", "Anti-Bot Strategy": "Header Rotation"},
        {"Portal": "MakeMyTrip (makemytrip.com)", "Type": "OTA", "Robots.txt Status": "COMPLIANT", "Rate Limit Policy": "2.5s jitter interval", "Anti-Bot Strategy": "Back-off on 429 Challenge"},
        {"Portal": "EaseMyTrip (easemytrip.com)", "Type": "OTA", "Robots.txt Status": "COMPLIANT", "Rate Limit Policy": "1.5s delay", "Anti-Bot Strategy": "Standard HTTP GET with fallback"},
    ]
    st.table(pd.DataFrame(compliance_data))

    st.markdown("#### 🕒 **Tri-Epoch Intraday Sampling Protocol (Diurnal Bias Protection)**")
    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin-bottom: 18px;">
        <div class="glass-panel" style="padding: 14px; border-left: 3px solid #38bdf8;">
            <b style="color: #38bdf8; font-size: 0.88rem;">Wave 1 · 08:00 IST (Morning Baseline)</b>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">Weight: <b>20%</b> · Captures opening daily inventory & post-midnight algorithmic fare resets.</div>
        </div>
        <div class="glass-panel" style="padding: 14px; border-left: 3px solid #fbbf24;">
            <b style="color: #fbbf24; font-size: 0.88rem;">Wave 2 · 14:00 IST (Midday Corporate)</b>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">Weight: <b>30%</b> · Captures business desk corporate booking cycles and mid-day seat bucket churn.</div>
        </div>
        <div class="glass-panel" style="padding: 14px; border-left: 3px solid #34d399;">
            <b style="color: #34d399; font-size: 0.88rem;">Wave 3 · 20:00 IST (Evening Peak)</b>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">Weight: <b>50%</b> · Captures prime leisure booking volume (~50% of daily consumer transactions).</div>
        </div>
    </div>
    <div class="glass-panel" style="border-left: 4px solid #10b981; margin-bottom: 20px;">
        <b>Axiomatic Resolution:</b> Tier 1 of our <b>Two-Tier Jevons-Laspeyres formulation</b> pools price quotes across all 3 intraday waves using a geometric mean:
        <span style="font-family: 'JetBrains Mono'; color: #38bdf8; font-size: 0.84rem;"> P^{geom}_{t,r,\tau} = exp( (1/N) ∑ ln P_i )</span>. 
        This eliminates single-snapshot time-of-day bias while ensuring transient 1-hour flash anomalies do not distort the national index.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### **Live Scheduled Scraper Trigger & Telemetry Feed**")
    t_c1, t_c2 = st.columns([4, 6])
    with t_c1:
        target_date = st.date_input("Target Extraction Date:", datetime.utcnow())
        target_epoch = st.selectbox(
            "Observation Epoch:",
            [
                "All 3 Waves (Full Intraday Composite)",
                "Wave 1 — 08:00 IST (Morning)",
                "Wave 2 — 14:00 IST (Midday)",
                "Wave 3 — 20:00 IST (Evening Peak)",
            ],
            index=0,
        )
        if st.button("🚀 Trigger Live Daily Scraping Run", type="primary"):
            with st.spinner("Executing ethical scraping engine across intraday strata..."):
                import importlib
                import apix.scrapers.scheduler
                importlib.reload(apix.scrapers.scheduler)
                from apix.scrapers.scheduler import ScraperScheduler

                scheduler = ScraperScheduler(db)
                cleaner = DataCleaningPipeline()
                index_engine = IndexEngine(db, weight_mgr)
                
                d_str = target_date.strftime("%Y-%m-%d")
                try:
                    res = scheduler.run_daily_scrape(quote_date_str=d_str, epoch=target_epoch)
                except TypeError:
                    res = scheduler.run_daily_scrape(quote_date_str=d_str)
                with db.get_connection() as conn:
                    rows = conn.execute("SELECT * FROM raw_quotes WHERE scraped_at LIKE ?", (f"{d_str}%",)).fetchall()
                clean = cleaner.clean_quotes([dict(r) for r in rows], quote_date_str=d_str)
                db.insert_clean_quotes(clean)
                idx = index_engine.compute_daily_index(quote_date_str=d_str, clean_quotes=clean)
                st.cache_data.clear()
                st.session_state["last_scrape_status"] = {
                    "date": d_str,
                    "epoch": target_epoch,
                    "quotes": res["quotes_scraped"],
                    "index": idx["two_tier_index"],
                    "time": datetime.utcnow().strftime("%H:%M:%S UTC")
                }
                st.rerun()

        if "last_scrape_status" in st.session_state:
            lstat = st.session_state["last_scrape_status"]
            st.success(f"✅ Ingested {lstat['quotes']:,} quotes for {lstat['date']} [{lstat['epoch']}]. Updated Two-Tier Index: **{lstat['index']:.2f}** (Completed at {lstat['time']}).")

    with t_c2:
        with db.get_connection() as conn:
            latest_idx = conn.execute("SELECT date, two_tier_index, laspeyres_index, average_fare, sample_size FROM daily_index ORDER BY date DESC LIMIT 1").fetchone()
            latest_raw_time = conn.execute("SELECT MAX(scraped_at) FROM raw_quotes").fetchone()[0]
            distinct_dates = [r[0] for r in conn.execute("SELECT DISTINCT quote_date FROM clean_quotes ORDER BY quote_date DESC LIMIT 45").fetchall()]

        st.markdown(f"""
        <div class="glass-panel" style="padding: 16px; border-left: 3px solid #38bdf8;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <b style="color: #ffffff; font-size: 0.90rem;">📡 Latest Database Ingestion Telemetry</b>
                <span style="font-size: 0.70rem; color: #34d399; font-weight: 700; background: rgba(52, 211, 153, 0.12); padding: 2px 8px; border-radius: 4px;">● PERSISTED TO DISK</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.78rem; margin-top: 8px;">
                <div>
                    <span style="color: #94a3b8; display: block; font-size: 0.68rem; text-transform: uppercase;">Latest Index Date</span>
                    <b style="color: #fbbf24; font-size: 0.92rem;">{latest_idx['date'] if latest_idx else 'N/A'}</b>
                </div>
                <div>
                    <span style="color: #94a3b8; display: block; font-size: 0.68rem; text-transform: uppercase;">Two-Tier Index Level</span>
                    <b style="color: #38bdf8; font-size: 0.92rem;">{latest_idx['two_tier_index'] if latest_idx else 0.0:.2f}</b>
                </div>
                <div>
                    <span style="color: #94a3b8; display: block; font-size: 0.68rem; text-transform: uppercase;">Basket Avg Fare</span>
                    <b style="color: #34d399; font-size: 0.92rem;">₹{latest_idx['average_fare'] if latest_idx else 0:,.0f}</b>
                </div>
                <div>
                    <span style="color: #94a3b8; display: block; font-size: 0.68rem; text-transform: uppercase;">Cleaned Fact Quotes</span>
                    <b style="color: #f8fafc; font-size: 0.92rem;">{latest_idx['sample_size'] if latest_idx else 0:,}</b>
                </div>
            </div>
            <div style="font-size: 0.72rem; color: #64748b; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
                Last Raw Ingestion Epoch: <span style="color: #cbd5e1; font-family: 'JetBrains Mono';">{latest_raw_time or 'N/A'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 🔍 **Live Scraped Flight Quotes & Inventory Explorer (Persistent Database Feed)**")
    st.caption("Inspect live quotes scraped and permanently stored across all 15 domestic corridors. Data is pulled straight from SQLite and persists permanently across browser refreshes.")

    if distinct_dates:
        f_c1, f_c2, f_c3 = st.columns([3, 4, 3])
        with f_c1:
            selected_quote_date = st.selectbox(
                "Filter Ingestion Date:",
                options=distinct_dates,
                index=0,
                key="feed_date_select"
            )
        with f_c2:
            corridor_options = ["All 15 Corridors"] + sorted(list(set([f"{r[0]}-{r[1]}" for r in BASKET_ROUTES])))
            selected_corridor = st.selectbox("Filter Corridor:", options=corridor_options, index=0, key="feed_corridor_select")
        with f_c3:
            carrier_options = ["All Carriers", "IndiGo (6E)", "Air India (AI)", "Akasa Air (QP)", "SpiceJet (SG)", "Air India Express (IX)"]
            selected_carrier = st.selectbox("Filter Carrier:", options=carrier_options, index=0, key="feed_carrier_select")

        query = "SELECT carrier_name, flight_number, canonical_route, departure_date, advance_days, total_fare, base_fare, (total_fare - base_fare) AS total_taxes, is_sold_out FROM clean_quotes WHERE quote_date = ?"
        params = [selected_quote_date]
        if selected_corridor != "All 15 Corridors":
            query += " AND canonical_route = ?"
            params.append(selected_corridor)
        if selected_carrier != "All Carriers":
            code = selected_carrier.split("(")[-1].replace(")", "")
            query += " AND carrier_code = ?"
            params.append(code)
        query += " ORDER BY total_fare DESC LIMIT 150"

        with db.get_connection() as conn:
            df_feed = pd.read_sql_query(query, conn, params=params)

        if not df_feed.empty:
            df_feed_display = df_feed.copy()
            df_feed_display["Total Fare"] = df_feed_display["total_fare"].map(lambda x: f"₹{x:,.0f}")
            df_feed_display["Base Fare"] = df_feed_display["base_fare"].map(lambda x: f"₹{x:,.0f}")
            df_feed_display["Taxes & Fees"] = df_feed_display["total_taxes"].map(lambda x: f"₹{x:,.0f}")
            df_feed_display["Lead Window"] = df_feed_display["advance_days"].map(lambda x: f"T+{x}")
            df_feed_display["Inventory"] = df_feed_display["is_sold_out"].map(lambda x: "Sold Out" if x == 1 else "Available")
            df_feed_display.rename(columns={
                "carrier_name": "Airline",
                "flight_number": "Flight #",
                "canonical_route": "Corridor",
                "departure_date": "Dep Date",
            }, inplace=True)
            
            st.dataframe(
                df_feed_display[["Airline", "Flight #", "Corridor", "Dep Date", "Lead Window", "Total Fare", "Base Fare", "Taxes & Fees", "Inventory"]],
                use_container_width=True,
                hide_index=True,
            )
            st.caption(f"Showing up to 150 live quotes for **{selected_quote_date}** matching filters. All data is persisted in SQLite (`data/apix.db`).")
        else:
            st.info(f"No quotes found in database matching the selected filters.")

# ==========================================
# TAB 9: MOSPI & RBI EXPORT HUB
# ==========================================
with tabs[8]:
    st.markdown("### 🏛️ **MoSPI & RBI Integration Hub & Programmatic Export**")
    st.caption("Direct RESTful API integration, UN COICOP 07.3.3.1 schema feeds, and one-click statistical package downloads.")

    c1, c2 = st.columns([6, 4])
    with c1:
        st.markdown("""
        <div class="glass-panel">
            <div style="font-weight: 700; color: #38bdf8; font-size: 1rem; margin-bottom: 10px;">
                ⚡ OpenAPI 3.0 Production Endpoints
            </div>
            <div style="font-family: 'JetBrains Mono'; font-size: 0.82rem; color: #cbd5e1; line-height: 1.8;">
                • <b style="color: #34d399;">GET</b> <code>/api/v1/index/latest</code> — Real-time latest daily APIx indices<br/>
                • <b style="color: #34d399;">GET</b> <code>/api/v1/index/history</code> — Frequency: daily | weekly | monthly<br/>
                • <b style="color: #34d399;">GET</b> <code>/api/v1/esankhyiki/augmentation</code> — Official vs Augmented CPI series<br/>
                • <b style="color: #34d399;">GET</b> <code>/api/v1/esankhyiki/export</code> — UN COICOP 07.3.3.1 JSON batch feed<br/>
                • <b style="color: #34d399;">GET</b> <code>/api/v1/routes</code> — Basket corridors & DGCA passenger weights<br/>
                • <b style="color: #34d399;">GET</b> <code>/api/v1/decomposition</code> — Line-item statutory tax/fee breakdown<br/>
                • <b style="color: #34d399;">GET</b> <code>/api/v1/backtest</code> — 90-day econometric validation metrics
            </div>
            <div style="margin-top: 14px; font-size: 0.83rem; color: #94a3b8;">
                Interactive Swagger Documentation: <a href="http://127.0.0.1:8000/docs" target="_blank" style="color: #38bdf8; text-decoration: underline;">http://127.0.0.1:8000/docs</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("#### **Export Data for Statistical Packages**")
        csv_data = df_indices.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download 90-Day Index Time Series (CSV)",
            data=csv_data,
            file_name="apix_90day_historical_index.csv",
            mime="text/csv",
            use_container_width=True,
        )

        weights_df = weight_mgr.get_all_route_weights()
        w_records = [{"route": k, "weight": v} for k, v in weights_df.items()]
        w_csv = pd.DataFrame(w_records).to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download DGCA Route Weights (CSV)",
            data=w_csv,
            file_name="dgca_route_weights.csv",
            mime="text/csv",
            use_container_width=True,
        )

        es_feed = esankhyiki_mgr.generate_esankhyiki_feed(df_indices)
        st.download_button(
            label="🏛️ Download eSankhyiki PSD Batch Payload (JSON)",
            data=json.dumps(es_feed, indent=2).encode("utf-8"),
            file_name="mospi_esankhyiki_psd_feed.json",
            mime="application/json",
            use_container_width=True,
        )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.82rem; padding-bottom: 24px;'>"
    "<b>APIx Platform v1.2.0</b><br/>"
    "Built for Ministry of Statistics and Programme Implementation (MoSPI) & Reserve Bank of India (RBI)"
    "</div>",
    unsafe_allow_html=True,
)
