import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import random
import json
import pickle
import os
import boto3
from botocore.exceptions import ClientError

st.set_page_config(page_title="DriftWatch", page_icon="📡",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  * { font-family: 'Inter', sans-serif; }

  [data-testid="stAppViewContainer"] { background: #0a0a0a; }
  [data-testid="stHeader"] { background: transparent; }
  section[data-testid="stSidebar"] { display: none; }
  [data-testid="stMainBlockContainer"] { padding: 0 1.5rem 2rem; }
  div[data-testid="stVerticalBlock"] > div { gap: 0; }

  /* Hide streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }

  /* Typography */
  h1,h2,h3,h4,p,label,span,.stMarkdown { color: #e5e5e5; }

  /* ── Top bar ── */
  .topbar {
    background: #171717;
    border-bottom: 1px solid #262626;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0 -1.5rem 20px;
  }
  .topbar-left { display: flex; align-items: center; gap: 12px; }
  .topbar-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #14b8a6, #2dd4bf);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
  }
  .topbar-title { color: #f5f5f5; font-size: 1rem; font-weight: 600; }
  .topbar-sub { color: #8b949e; font-size: 0.75rem; }
  .drift-badge {
    background: #3d1f00; border: 1px solid #d29922;
    color: #d29922; border-radius: 20px;
    padding: 5px 14px; font-size: 0.78rem; font-weight: 600;
    display: flex; align-items: center; gap: 6px;
  }
  .topbar-right { display: flex; align-items: center; gap: 16px; }
  .last-updated { color: #8b949e; font-size: 0.75rem; text-align: right; }

  /* ── KPI cards ── */
  .kpi-card {
    background: #171717;
    border: 1px solid #262626;
    border-radius: 10px;
    padding: 18px 20px;
    height: 100%;
  }
  .kpi-label { color: #8b949e; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
  .kpi-value { font-size: 1.75rem; font-weight: 700; color: #f5f5f5; margin-bottom: 4px; }
  .kpi-value.orange { color: #d29922; }
  .kpi-value.red    { color: #f85149; }
  .kpi-value.green  { color: #3fb950; }
  .kpi-value.muted  { color: #484f58; font-size: 1.1rem; font-weight: 500; padding-top: 6px; }
  .kpi-delta { font-size: 0.75rem; color: #8b949e; }
  .kpi-delta.down { color: #f85149; }

  /* ── Tabs ── */
  [data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #262626;
    gap: 0;
    margin-bottom: 20px;
  }
  [data-testid="stTabs"] button {
    color: #8b949e !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 10px 16px !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
  }
  [data-testid="stTabs"] button:hover { color: #e5e5e5 !important; }
  [data-testid="stTabs"] button[aria-selected="true"] {
    color: #f5f5f5 !important;
    border-bottom: 2px solid #14b8a6 !important;
    font-weight: 600 !important;
  }

  /* ── Cards ── */
  .card {
    background: #171717;
    border: 1px solid #262626;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
  }
  .card-title { color: #f5f5f5; font-size: 0.9rem; font-weight: 600; margin-bottom: 2px; }
  .card-sub   { color: #8b949e; font-size: 0.75rem; margin-bottom: 14px; }

  /* ── Buttons — default (indigo) ── */
  .stButton > button {
    background: #0d9488 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1.2rem !important;
    width: 100%;
    transition: background 0.15s, border-color 0.15s, color 0.15s ease !important;
  }
  .stButton > button:hover { background: #0f766e !important; }

  /* ── Form submit buttons (indigo, matches regular) ── */
  [data-testid="stFormSubmitButton"] button {
    background: #0d9488 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1.2rem !important;
    width: 100%;
    transition: background 0.15s ease !important;
  }
  [data-testid="stFormSubmitButton"] button:hover { background: #0f766e !important; }

  /* ── Post Ground Truth — green ── */
  div:has(> #gt-btn-marker) ~ div [data-testid="stButton"] > button,
  div:has(> #gt-btn-marker) + div [data-testid="stButton"] > button {
    background: #059669 !important;
    border: none !important;
    color: #fff !important;
  }
  div:has(> #gt-btn-marker) ~ div [data-testid="stButton"] > button:hover,
  div:has(> #gt-btn-marker) + div [data-testid="stButton"] > button:hover {
    background: #047857 !important;
  }

  /* ── Secondary / outline buttons ── */
  div:has(> #sec-test-marker) ~ div [data-testid="stButton"] > button,
  div:has(> #sec-test-marker) + div [data-testid="stButton"] > button,
  div:has(> #fetch-btn-marker) ~ div [data-testid="stButton"] > button,
  div:has(> #fetch-btn-marker) + div [data-testid="stButton"] > button {
    background: rgba(15,23,42,0.5) !important;
    border: 1px solid #404040 !important;
    color: #d4d4d4 !important;
  }
  div:has(> #sec-test-marker) ~ div [data-testid="stButton"] > button:hover,
  div:has(> #sec-test-marker) + div [data-testid="stButton"] > button:hover,
  div:has(> #fetch-btn-marker) ~ div [data-testid="stButton"] > button:hover,
  div:has(> #fetch-btn-marker) + div [data-testid="stButton"] > button:hover {
    background: #1a1a1a !important;
    border-color: #525252 !important;
    color: #f5f5f5 !important;
  }

  /* ── Reset / muted charcoal button ── */
  div:has(> #reset-btn-marker) ~ div [data-testid="stButton"] > button,
  div:has(> #reset-btn-marker) + div [data-testid="stButton"] > button {
    background: #262626 !important;
    border: 1px solid #404040 !important;
    color: #8b949e !important;
  }
  div:has(> #reset-btn-marker) ~ div [data-testid="stButton"] > button:hover,
  div:has(> #reset-btn-marker) + div [data-testid="stButton"] > button:hover {
    background: #292929 !important;
    color: #e5e5e5 !important;
  }

  /* ── Form inputs — unified slate-700 borders ── */
  [data-testid="stSelectbox"] > div > div,
  [data-testid="stSelectbox"] > div > div > div,
  [data-testid="stTextInput"] input,
  [data-testid="stTextInput"] > div > div > input,
  [data-testid="stTextInput"] > div > div,
  [data-testid="stNumberInput"] input {
    background: #0a0a0a !important;
    border: 1px solid #404040 !important;
    border-radius: 6px !important;
    color: #f5f5f5 !important;
    font-size: 0.85rem !important;
  }
  [data-testid="stTextInput"] input:focus,
  [data-testid="stTextInput"] > div > div:focus-within {
    border-color: #0d9488 !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(20,184,166,0.25) !important;
  }
  [data-testid="stTextInput"] input::placeholder { color: #484f58 !important; }
  [data-testid="stForm"] { background: transparent !important; border: none !important; padding: 0 !important; }

  /* ── Dropdown overlay (popover + menu) ── */
  /* Popover wrapper — may mount as a body-level portal */
  [data-baseweb="popover"],
  [data-baseweb="popover"] > div {
    background: #171717 !important;
    border: 1px solid #262626 !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
  }
  /* Menu list container */
  [data-baseweb="menu"],
  [data-baseweb="menu"] ul,
  [role="listbox"] {
    background: #171717 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 4px !important;
  }
  /* Individual option items */
  [data-baseweb="menu"] li,
  [data-baseweb="menu"] [role="option"],
  [role="option"] {
    background: #171717 !important;
    color: #e5e5e5 !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    padding: 8px 12px !important;
    cursor: pointer !important;
  }
  /* Hover state */
  [data-baseweb="menu"] li:hover,
  [data-baseweb="menu"] [role="option"]:hover,
  [role="option"]:hover {
    background: #262626 !important;
    color: #f5f5f5 !important;
  }
  /* Selected / active state */
  [data-baseweb="menu"] [aria-selected="true"],
  [role="option"][aria-selected="true"] {
    background: rgba(20,184,166,0.15) !important;
    color: #5eead4 !important;
    font-weight: 600 !important;
  }
  /* Highlighted (keyboard nav) */
  [data-baseweb="menu"] li[data-highlighted="true"],
  [role="option"][data-highlighted="true"] {
    background: #262626 !important;
    color: #f5f5f5 !important;
  }
  /* Scrollbar inside dropdown */
  [data-baseweb="menu"] ul::-webkit-scrollbar { width: 4px; }
  [data-baseweb="menu"] ul::-webkit-scrollbar-track { background: #171717; }
  [data-baseweb="menu"] ul::-webkit-scrollbar-thumb { background: #404040; border-radius: 4px; }

  /* ── Slider ── */
  [data-testid="stSlider"] { margin-bottom: 4px; }
  .stSlider .st-ae { background: #14b8a6; }

  /* ── Section label ── */
  .sec-label {
    color: #8b949e; font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em;
    margin: 14px 0 6px;
  }

  /* ── Alert rows ── */
  .alert-row {
    background: #0a0a0a; border: 1px solid #262626; border-radius: 8px;
    padding: 10px 14px; margin-bottom: 8px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .alert-model { color: #f5f5f5; font-size: 0.85rem; font-weight: 600; }
  .alert-detail { color: #8b949e; font-size: 0.75rem; margin-top: 2px; }
  .badge { border-radius: 20px; padding: 3px 10px; font-size: 0.72rem; font-weight: 700; display: inline-block; }
  .badge-healthy   { background: #0f2d17; color: #3fb950; border: 1px solid #238636; }
  .badge-critical  { background: #2d0f0f; color: #f85149; border: 1px solid #da3633; }
  .badge-watch     { background: #2d2006; color: #d29922; border: 1px solid #9e6a03; }
  .badge-active    { background: #042f2e; color: #14b8a6; border: 1px solid #0f766e; }
  .badge-live      { background: #0f2d17; color: #3fb950; border: 1px solid #238636; }

  /* ── Step row ── */
  .step-row {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 10px 0; border-bottom: 1px solid #262626;
  }
  .step-row:last-child { border-bottom: none; }
  .step-num {
    width: 26px; height: 26px; border-radius: 50%;
    background: #1f2937; border: 1px solid #374151;
    color: #9ca3af; font-size: 0.75rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .step-num.blue   { background: #042f2e; border-color: #0f766e; color: #14b8a6; }
  .step-num.green  { background: #0f2d17; border-color: #238636; color: #3fb950; }
  .step-num.yellow { background: #2d2006; border-color: #9e6a03; color: #d29922; }
  .step-num.red    { background: #2d0f0f; border-color: #da3633; color: #f85149; }
  .step-title { color: #f5f5f5; font-size: 0.85rem; font-weight: 600; }
  .step-sub   { color: #8b949e; font-size: 0.75rem; }

  /* ── Kinesis metrics ── */
  .kinesis-metrics {
    display: flex; gap: 0;
    border-top: 1px solid #262626; margin-top: 12px;
  }
  .km-cell {
    flex: 1; padding: 12px 16px; border-right: 1px solid #262626; text-align: center;
  }
  .km-cell:last-child { border-right: none; }
  .km-val   { color: #14b8a6; font-size: 1.2rem; font-weight: 700; }
  .km-label { color: #8b949e; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }

  /* ── Phase cards ── */
  .phase-card {
    background: #0a0a0a; border: 1px solid #262626;
    border-radius: 8px; padding: 14px; margin-bottom: 10px;
    border-top-width: 2px;
  }
  .phase-card.pc-green  { border-top-color: #3fb950; }
  .phase-card.pc-yellow { border-top-color: #d29922; }
  .phase-card.pc-orange { border-top-color: #e06c00; }
  .phase-card.pc-red    { border-top-color: #f85149; }
  .phase-card.pc-green  .phase-name { color: #3fb950; }
  .phase-card.pc-yellow .phase-name { color: #d29922; }
  .phase-card.pc-orange .phase-name { color: #e06c00; }
  .phase-card.pc-red    .phase-name { color: #f85149; }
  .phase-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
  .phase-name { font-size: 0.88rem; font-weight: 600; }
  .phase-badge {
    width: 24px; height: 24px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; font-weight: 700; flex-shrink: 0;
  }
  .p1 { background: #0f2d17; color: #3fb950; border: 1px solid #238636; }
  .p2 { background: #2d2006; color: #d29922; border: 1px solid #9e6a03; }
  .p3 { background: #2d1a06; color: #e06c00; border: 1px solid #9e4a03; }
  .p4 { background: #2d0f0f; color: #f85149; border: 1px solid #da3633; }
  .phase-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
  .phase-lbl { color: #8b949e; font-size: 0.75rem; }
  .phase-val { color: #e5e5e5; font-size: 0.75rem; font-weight: 600; }

  /* ── Textarea ── */
  [data-testid="stTextArea"] textarea {
    background: #0a0a0a !important;
    border: 1px solid #404040 !important;
    border-radius: 6px !important;
    color: #f5f5f5 !important;
    font-size: 0.85rem !important;
    resize: vertical !important;
  }
  [data-testid="stTextArea"] textarea:focus {
    border-color: #0d9488 !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(20,184,166,0.25) !important;
  }
  [data-testid="stTextArea"] textarea::placeholder { color: #484f58 !important; }

  /* ── Progress bar ── */
  [data-testid="stProgress"] > div > div { background: #14b8a6 !important; }

  /* ── Status text ── */
  .status-line { background: #171717; border: 1px solid #262626; border-radius: 8px; padding: 10px 16px; font-size: 0.82rem; color: #8b949e; margin-bottom: 10px; }
  .status-line strong { color: #f5f5f5; }

  hr { border-color: #262626; margin: 12px 0; }

  /* ── HTML table (replaces st.dataframe) ── */
  .pred-table { width:100%; border-collapse:collapse; font-size:0.82rem; }
  .pred-table th { background:#1c1c1c; color:#8b949e; font-weight:600; font-size:0.72rem;
    text-transform:uppercase; letter-spacing:0.06em; padding:10px 14px; text-align:left;
    border-bottom:1px solid #404040; }
  .pred-table td { padding:9px 14px; border-bottom:1px solid #262626; color:#e5e5e5; vertical-align:middle; }
  .pred-table tr:last-child td { border-bottom:none; }
  .pred-table tr:hover td { background:#1c1c1c; }
  .conf-badge { border-radius:20px; padding:2px 10px; font-size:0.75rem; font-weight:600; display:inline-block; }
  .conf-green  { background:#0f2d17; color:#3fb950; border:1px solid #238636; }
  .conf-yellow { background:#2d2006; color:#d29922; border:1px solid #9e6a03; }
  .conf-red    { background:#2d0f0f; color:#f85149; border:1px solid #da3633; }

  /* ── Chart section headers ── */
  .chart-hdr { margin-bottom:6px; }
  .chart-hdr-title { color:#f5f5f5; font-size:0.88rem; font-weight:600; }
  .chart-hdr-sub   { color:#8b949e; font-size:0.73rem; margin-top:1px; }

  /* ── Live dot ── */
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  .live-dot { display:inline-block; width:7px; height:7px; border-radius:50%;
    background:#3fb950; margin-right:5px; animation:pulse 2s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
API_URL = "https://pxwyjr8f53.execute-api.us-east-1.amazonaws.com/prod"
API_KEY = "M8y3JhMAIg7GZuYEGrShm7yOaOrYOSz45WF4yUPj"
HEADERS = {"Content-Type": "application/json", "x-api-key": API_KEY}

CHART = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8b949e", size=11),
    xaxis=dict(gridcolor="#262626", linecolor="#404040", tickfont=dict(color="#8b949e")),
    yaxis=dict(gridcolor="#262626", linecolor="#404040", tickfont=dict(color="#8b949e")),
    margin=dict(l=10, r=10, t=30, b=10),
)
CHART_CARD = dict(
    paper_bgcolor="#111111", plot_bgcolor="#111111",
    font=dict(color="#8b949e", size=11),
    xaxis=dict(gridcolor="#262626", linecolor="#404040", tickfont=dict(color="#8b949e")),
    yaxis=dict(gridcolor="#262626", linecolor="#404040", tickfont=dict(color="#8b949e")),
    margin=dict(l=10, r=10, t=10, b=10),
)

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in [("predictions", []), ("ground_truth", []), ("drift_alerts", []), ("db_loaded", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

def load_from_dynamodb():
    try:
        table = boto3.resource("dynamodb", region_name="us-east-1").Table("ml-predictions")
        resp = table.scan(Limit=300)
        return [
            {
                "id":         i.get("id", ""),
                "model_id":   i.get("model_id", "unknown"),
                "timestamp":  i.get("timestamp", ""),
                "prediction": i.get("prediction", ""),
                "confidence": float(i.get("confidence", 0)),
                "source":     i.get("source", "api"),
            }
            for i in resp.get("Items", [])
        ]
    except (ClientError, Exception):
        return []

if not st.session_state.db_loaded:
    hist = load_from_dynamodb()
    if hist:
        existing = {p.get("id") for p in st.session_state.predictions}
        for item in hist:
            if item["id"] not in existing:
                st.session_state.predictions.append(item)
    st.session_state.db_loaded = True

# ── Helpers ────────────────────────────────────────────────────────────────────
def api_post(path, body):
    try:
        r = requests.post(f"{API_URL}{path}", headers=HEADERS, json=body, timeout=8)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def api_get(path):
    try:
        r = requests.get(f"{API_URL}{path}", headers=HEADERS, timeout=8)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def conf_color(v):
    if v >= 0.75: return "#3fb950"
    if v >= 0.60: return "#d29922"
    return "#f85149"

def conf_badge(v):
    c = conf_color(v)
    label = "Healthy" if v >= 0.75 else ("Warning" if v >= 0.60 else "Critical")
    return f'<span style="color:{c};font-weight:600;">● {label}  {v:.0%}</span>'

# ── Derived stats ──────────────────────────────────────────────────────────────
preds    = st.session_state.predictions
df       = pd.DataFrame(preds) if preds else pd.DataFrame()
total    = len(df)
avg_conf = float(df["confidence"].mean()) if not df.empty else 0.0
low_conf = int((df["confidence"] < 0.75).sum()) if not df.empty else 0
n_models = df["model_id"].nunique() if not df.empty else 0
gt_items = st.session_state.ground_truth
gt_acc   = (sum(1 for g in gt_items if g.get("correct")) / len(gt_items)) if gt_items else None
drifting = avg_conf < 0.75 and total > 0

# ── Top bar ────────────────────────────────────────────────────────────────────
badge_html = (
    '<span class="drift-badge">⚠ DRIFT DETECTED</span>'
    if drifting else
    '<span style="background:#0f2d17;border:1px solid #238636;color:#3fb950;border-radius:20px;padding:5px 14px;font-size:0.78rem;font-weight:600;">● SYSTEM HEALTHY</span>'
)
DRIFTWATCH_LOGO = """
<svg width="42" height="42" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="dw_bg" x1="0" y1="0" x2="42" y2="42" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#042f2e"/>
      <stop offset="100%" stop-color="#0a0a0a"/>
    </linearGradient>
    <linearGradient id="dw_wave" x1="4" y1="0" x2="38" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#0d9488"/>
      <stop offset="60%" stop-color="#14b8a6"/>
      <stop offset="100%" stop-color="#f85149"/>
    </linearGradient>
  </defs>
  <!-- App icon background -->
  <rect width="42" height="42" rx="11" fill="url(#dw_bg)"/>
  <rect width="42" height="42" rx="11" fill="#0d9488" fill-opacity="0.08"/>
  <!-- Baseline grid line -->
  <line x1="5" y1="25" x2="37" y2="25" stroke="#262626" stroke-width="1"/>
  <!-- Waveform: stable heartbeat then drifts downward -->
  <path d="M5 21 L9 21 L11 15 L14 27 L17 21 L20 21 L23 23 L26 27 L29 30 L33 30"
        stroke="url(#dw_wave)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <!-- Drift alert dot (red, at end of drift) -->
  <circle cx="33" cy="30" r="3.2" fill="#f85149"/>
  <circle cx="33" cy="30" r="1.4" fill="#fff" fill-opacity="0.9"/>
</svg>"""

st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <div class="topbar-icon" style="background:none;padding:0;width:42px;height:42px;">{DRIFTWATCH_LOGO}</div>
    <div>
      <div class="topbar-title">DriftWatch</div>
      <div class="topbar-sub">Serverless ML monitoring · real-time drift detection &amp; model reliability on AWS</div>
    </div>
  </div>
  <div class="topbar-right">
    {badge_html}
    <div class="last-updated">Last updated<br><strong style="color:#f5f5f5">{datetime.utcnow().strftime('%H:%M:%S UTC')}</strong></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI strip ──────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5, gap="small")
for col, label, val, cls, delta in [
    (c1, "TOTAL PREDICTIONS",    f"{total:,}",                  "",       ""),
    (c2, "AVG CONFIDENCE",       f"{avg_conf:.2f}",             "orange" if avg_conf < 0.75 else "", f'▼ {abs(avg_conf-0.85):.1%} vs baseline' if total else ""),
    (c3, "LOW-CONFIDENCE",       f"{low_conf:,}",               "red" if low_conf else "", ""),
    (c4, "MODELS MONITORED",     f"{n_models} Active" if n_models else "—", "", ""),
    (c5, "GROUND TRUTH ACCURACY",f"{gt_acc:.1%}" if gt_acc else "Pending", "green" if gt_acc and gt_acc>=0.8 else "muted", "Awaiting human labels" if not gt_acc else ""),
]:
    with col:
        if delta and delta.startswith("Awaiting"):
            d_html = f'<div style="font-size:0.72rem;color:#484f58;margin-top:4px;">{delta}</div>'
        elif delta:
            d_html = f'<div class="kpi-delta down">{delta}</div>'
        else:
            d_html = ""
        st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value {cls}">{val}</div>
  {d_html}
</div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5 = st.tabs(["  Live Monitor  ", "  Drift Control  ", "  Configure  ", "  Simulate Drift  ", "  Live Classifier  "])

# ══════════════════════════════════════════════════════
# TAB 1 — LIVE MONITOR
# ══════════════════════════════════════════════════════
with t1:
    # ── Status bar + Refresh ─────────────────────────────────────────────────
    sb1, sb2 = st.columns([7, 1])
    with sb1:
        st.markdown(
            f'<div style="padding:6px 0;color:#8b949e;font-size:0.82rem;">'
            f'<span class="live-dot"></span>Live · <strong style="color:#f5f5f5">{total:,}</strong> predictions '
            f'· avg confidence <strong style="color:{conf_color(avg_conf) if total else "#8b949e"}">{avg_conf:.2f}</strong>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with sb2:
        if st.button("↻ Refresh", use_container_width=True, help="Reload from DynamoDB"):
            fresh = load_from_dynamodb()
            if fresh:
                existing = {p.get("id") for p in st.session_state.predictions}
                added = sum(1 for item in fresh if item["id"] not in existing and
                            not st.session_state.predictions.append(item))
                st.toast(f"+{added} new predictions" if added else "Already up to date",
                         icon="✅" if added else "ℹ️")
            else:
                st.toast("DynamoDB unreachable — credentials may need refresh", icon="⚠️")
            st.rerun()

    if df.empty:
        st.markdown("""
<div style="background:#171717;border:1px solid #262626;border-radius:10px;
  padding:48px;text-align:center;margin-top:16px;">
  <div style="font-size:2.5rem;margin-bottom:12px;">📡</div>
  <div style="color:#f5f5f5;font-weight:600;font-size:1rem;margin-bottom:6px;">No predictions loaded yet</div>
  <div style="color:#8b949e;font-size:0.85rem;">Click <strong style="color:#14b8a6">↻ Refresh</strong> to load from DynamoDB,
  or go to <strong style="color:#14b8a6">Simulate Drift</strong> to generate live data</div>
</div>""", unsafe_allow_html=True)
    else:
        df_s = df.sort_values("timestamp")

        # ── Confidence over time ─────────────────────────────────────────────
        at1, at2 = st.columns([6, 2])
        with at1:
            st.markdown('<div class="chart-hdr"><div class="chart-hdr-title">Confidence Over Time</div>'
                        '<div class="chart-hdr-sub">Rolling window · mean prediction confidence per model</div></div>',
                        unsafe_allow_html=True)
        with at2:
            st.markdown('<div style="text-align:right;padding-top:4px;">'
                        '<span style="background:#2d2006;border:1px solid #9e6a03;color:#d29922;'
                        'border-radius:6px;padding:4px 10px;font-size:0.72rem;font-weight:600;">⚠ Alert Limit 0.75</span>'
                        '</div>', unsafe_allow_html=True)

        # Use only the most recent 150 predictions so fresh low-confidence data
        # isn't compressed into a sliver by hours of old historical data
        df_chart = df_s.tail(150)

        colors = ["#14b8a6", "#3fb950", "#d29922", "#2dd4bf", "#f85149"]
        fig_area = go.Figure()
        for i, mid in enumerate(df_chart["model_id"].unique()):
            sub = df_chart[df_chart["model_id"] == mid]
            c = colors[i % len(colors)]
            fig_area.add_trace(go.Scatter(
                x=sub["timestamp"], y=sub["confidence"],
                name=mid, mode="lines+markers",
                line=dict(color=c, width=2),
                marker=dict(color=c, size=4, opacity=0.7),
            ))
        fig_area.add_hline(y=0.75, line_dash="dash", line_color="#d29922", line_width=1.5,
                           annotation_text="Alert Limit", annotation_font_color="#d29922",
                           annotation_position="right")
        y_min = max(0.0, float(df_chart["confidence"].min()) - 0.05)
        y_max = min(1.0, float(df_chart["confidence"].max()) + 0.05)
        fig_area.update_layout(**CHART_CARD, height=240,
                               yaxis_range=[y_min, y_max],
                               legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h",
                                           yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_area, use_container_width=True, config={"displayModeBar": False})

        # ── 3 chart columns ──────────────────────────────────────────────────
        ca, cb, cc = st.columns(3, gap="small")

        with ca:
            st.markdown('<div class="chart-hdr"><div class="chart-hdr-title">Prediction Distribution</div>'
                        f'<div class="chart-hdr-sub">Across {total:,} predictions</div></div>',
                        unsafe_allow_html=True)
            dist = df["prediction"].value_counts().reset_index()
            dist.columns = ["label", "count"]
            fig_pie = go.Figure(go.Pie(
                labels=dist["label"], values=dist["count"], hole=0.58,
                marker_colors=["#14b8a6", "#3fb950", "#d29922", "#2dd4bf", "#f85149"],
                textfont_color="#e5e5e5", textfont_size=11,
            ))
            fig_pie.update_layout(**CHART_CARD, height=220, showlegend=True,
                                  legend=dict(bgcolor="rgba(0,0,0,0)", font_color="#8b949e",
                                              orientation="h", y=-0.08))
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

        with cb:
            st.markdown('<div class="chart-hdr"><div class="chart-hdr-title">Confidence Distribution</div>'
                        '<div class="chart-hdr-sub">Threshold 0.75</div></div>', unsafe_allow_html=True)
            fig_hist = go.Figure()
            above = df[df["confidence"] >= 0.75]["confidence"]
            below = df[df["confidence"] < 0.75]["confidence"]
            if not above.empty:
                fig_hist.add_trace(go.Histogram(x=above, nbinsx=12,
                    marker_color="#14b8a6", name="≥ 0.75", opacity=0.85))
            if not below.empty:
                fig_hist.add_trace(go.Histogram(x=below, nbinsx=8,
                    marker_color="#f85149", name="< 0.75", opacity=0.85))
            fig_hist.add_vline(x=0.75, line_dash="dash", line_color="#d29922", line_width=1.5)
            fig_hist.update_layout(**CHART_CARD, height=220, barmode="overlay", showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

        with cc:
            st.markdown('<div class="chart-hdr"><div class="chart-hdr-title">Avg Confidence by Model</div>'
                        '<div class="chart-hdr-sub">Mean over current window</div></div>',
                        unsafe_allow_html=True)
            mavg = df.groupby("model_id")["confidence"].mean().reset_index().sort_values("confidence")
            n_bars = len(mavg)
            bar_height = min(0.45, 0.9 / max(n_bars, 1))
            chart_h = max(120, min(220, n_bars * 60 + 60))
            fig_bar = go.Figure(go.Bar(
                y=mavg["model_id"], x=mavg["confidence"], orientation="h",
                width=bar_height,
                marker_color=[conf_color(v) for v in mavg["confidence"]],
                marker_line_width=0,
                text=[f"{v:.2f}" for v in mavg["confidence"]],
                textposition="inside", textfont_color="#0a0a0a", textfont_size=11,
            ))
            fig_bar.add_vline(x=0.75, line_dash="dash", line_color="#d29922", line_width=1.5)
            fig_bar.update_layout(**CHART_CARD, height=chart_h, xaxis_range=[0, 1],
                                  bargap=0.5)
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

        # ── Predictions table (HTML — no white background) ────────────────────
        st.markdown('<div style="margin-top:6px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-hdr"><div class="chart-hdr-title">Recent Ingested Predictions</div>'
                    '<div class="chart-hdr-sub">Latest 12 · auto-updates when new data arrives</div></div>',
                    unsafe_allow_html=True)

        show = df.sort_values("timestamp", ascending=False).head(12).copy()
        try:
            show["timestamp"] = pd.to_datetime(show["timestamp"]).dt.strftime("%H:%M:%S")
        except Exception:
            pass

        def _conf_badge(v):
            v = float(v)
            cls = "conf-green" if v >= 0.75 else ("conf-yellow" if v >= 0.60 else "conf-red")
            return f'<span class="conf-badge {cls}">{v:.3f}</span>'

        rows_html = ""
        for _, r in show.iterrows():
            rows_html += (
                f"<tr>"
                f"<td style='color:#8b949e'>{r.get('timestamp','')}</td>"
                f"<td><span style='color:#79c0ff;font-weight:600'>{r.get('model_id','')}</span></td>"
                f"<td>{r.get('prediction','')}</td>"
                f"<td>{_conf_badge(r.get('confidence', 0))}</td>"
                f"</tr>"
            )

        st.markdown(f"""
<div style="background:#171717;border:1px solid #262626;border-radius:10px;overflow:hidden;">
<table class="pred-table">
  <thead><tr>
    <th>TIMESTAMP</th><th>MODEL ID</th><th>PREDICTION</th><th>CONFIDENCE</th>
  </tr></thead>
  <tbody>{rows_html}</tbody>
</table>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# TAB 2 — DRIFT CONTROL
# ══════════════════════════════════════════════════════
with t2:
    left, right = st.columns([1, 1], gap="large")

    with left:
        # Send prediction
        st.markdown('<div class="card-title">Send a Live Prediction</div>'
                    '<div class="card-sub" style="margin-bottom:10px;">Ingestor simulation</div>',
                    unsafe_allow_html=True)

        with st.form("pred_form"):
            st.markdown('<div class="sec-label">MODEL ID</div>', unsafe_allow_html=True)
            model_id = st.selectbox("", ["spam-detector-v1", "fraud-detector-v3",
                                          "click-predictor-v2", "recommendation-engine-v4"],
                                    label_visibility="collapsed")
            st.markdown('<div class="sec-label">PREDICTION LABEL</div>', unsafe_allow_html=True)
            pred_label = st.selectbox("", ["Spam", "Ham", "Fraud", "Legit", "Click", "No-Click"],
                                      label_visibility="collapsed", key="pred_lbl")
            st.markdown('<div class="sec-label">CONFIDENCE SCORE</div>', unsafe_allow_html=True)
            confidence = st.slider("", 0.0, 1.0, 0.82, 0.01, label_visibility="collapsed")
            if confidence >= 0.75:
                status_txt   = "Healthy — above threshold"
                status_color = "#3fb950"
            elif confidence >= 0.65:
                status_txt   = "Warning — approaching threshold"
                status_color = "#d29922"
            else:
                status_txt   = "Drifting — below threshold"
                status_color = "#f85149"
            st.markdown(
                f'<div style="font-size:0.78rem;margin-bottom:8px;color:#8b949e;">'
                f'Status: <span style="color:{status_color};font-weight:600;">{status_txt}</span></div>',
                unsafe_allow_html=True,
            )
            submit = st.form_submit_button("Submit Prediction", use_container_width=True)

        if submit:
            res, code = api_post("/predictions", {
                "model_id": model_id, "prediction": pred_label.lower(), "confidence": confidence
            })
            if code == 200:
                st.session_state.predictions.append({
                    "id": res["id"], "model_id": model_id,
                    "prediction": pred_label.lower(), "confidence": confidence,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                st.success(f"Logged · ID `{res['id'][:10]}…`")
                st.rerun()
            else:
                st.error(str(res))

        st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)

        # Security test
        st.markdown("""
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
    <div>
      <div class="card-title">API Gateway Security Boundary Test</div>
      <div class="card-sub" style="margin-bottom:0">Validates auth enforcement on /predict</div>
    </div>
    <span class="badge badge-watch">Quarantine</span>
  </div>
  <div style="color:#8b949e;font-size:0.8rem;margin-bottom:12px;line-height:1.6;">
    Sends a synthetic request without an API key to verify that API Gateway rejects unauthenticated calls with HTTP 403.
  </div>
</div>""", unsafe_allow_html=True)
        st.markdown('<div id="sec-test-marker"></div>', unsafe_allow_html=True)
        if st.button("Try Request Without API Key", key="sec_test"):
            r = requests.post(f"{API_URL}/predictions",
                              headers={"Content-Type": "application/json"},
                              json={"model_id": "x", "prediction": "x", "confidence": 0.9})
            if r.status_code == 403:
                st.success(f"✅  403 Forbidden — API Gateway correctly blocked the unauthenticated request")
            else:
                st.warning(f"Unexpected {r.status_code}")

        # Ground truth
        st.markdown('<div class="card-title" style="margin-top:4px;">Submit Ground Truth Feedback</div>'
                    '<div class="card-sub" style="margin-bottom:10px;">Improves accuracy calibration</div>',
                    unsafe_allow_html=True)
        if preds:
            opts = {f"{p['id'][:12]}… · {p['model_id']}": p for p in preds[-20:]}
            st.markdown('<div class="sec-label">PREDICTION ID</div>', unsafe_allow_html=True)
            sel_key  = st.selectbox("", list(opts.keys()), label_visibility="collapsed", key="gt_sel")
            selected = opts[sel_key]
            st.markdown('<div class="sec-label">ACTUAL LABEL</div>', unsafe_allow_html=True)
            actual   = st.text_input("", placeholder="e.g. Spam", label_visibility="collapsed", key="gt_actual")
            # Marker div so the :has() CSS selector can target this button specifically
            st.markdown('<div id="gt-btn-marker"></div>', unsafe_allow_html=True)
            gt_sub = st.button("Post Ground Truth", use_container_width=True, key="gt_sub_btn")
            if gt_sub and actual:
                res, code = api_post("/ground-truth", {
                    "prediction_id": selected["id"], "model_id": selected["model_id"],
                    "actual_label": actual.lower(),
                })
                if "correct" in res:
                    st.session_state.ground_truth.append({
                        "model_id": selected["model_id"],
                        "predicted": selected["prediction"],
                        "actual": actual.lower(),
                        "correct": res["correct"],
                    })
                    icon = "✅" if res["correct"] else "❌"
                    st.info(f"{icon}  Predicted '{res['predicted']}' · Actual '{res['actual']}'")
        else:
            st.markdown('<div style="color:#8b949e;font-size:0.82rem;">Send predictions first to submit ground truth.</div>', unsafe_allow_html=True)

    with right:
        # Drift Detection Engine
        st.markdown("""
<div class="card">
  <div class="card-title">Drift Detection Engine</div>
  <div class="card-sub">Population Stability Index (PSI)</div>
  <div style="display:flex;flex-direction:column;gap:7px;">
    <div style="display:flex;gap:8px;align-items:flex-start;"><span style="color:#14b8a6;margin-top:2px;">▸</span><span style="color:#e5e5e5;font-size:0.82rem;">Computes PSI between rolling baseline and live feature windows</span></div>
    <div style="display:flex;gap:8px;align-items:flex-start;"><span style="color:#14b8a6;margin-top:2px;">▸</span><span style="color:#e5e5e5;font-size:0.82rem;">Bucketizes both distributions into deciles, then sums (P − Q) · ln(P/Q)</span></div>
    <div style="display:flex;gap:8px;align-items:flex-start;"><span style="color:#14b8a6;margin-top:2px;">▸</span><span style="color:#e5e5e5;font-size:0.82rem;">PSI &lt; 0.1 = stable · 0.1–0.2 = moderate drift · &gt; 0.2 = severe drift</span></div>
    <div style="display:flex;gap:8px;align-items:flex-start;"><span style="color:#14b8a6;margin-top:2px;">▸</span><span style="color:#e5e5e5;font-size:0.82rem;">Severe drift triggers SNS escalation + Step Functions retraining workflow</span></div>
  </div>
</div>""", unsafe_allow_html=True)

        # Recent Analytical Alerts
        alerts_html = ""
        if st.session_state.drift_alerts:
            for a in st.session_state.drift_alerts[-3:]:
                cls = "badge-critical" if a.get("critical") else "badge-healthy"
                lbl = "CRITICAL" if a.get("critical") else "HEALTHY"
                alerts_html += f"""
<div class="alert-row">
  <div><div class="alert-model">{a['model']}</div><div class="alert-detail">{a['detail']}</div></div>
  <span class="badge {cls}">{lbl}</span>
</div>"""
        else:
            alerts_html = """
<div class="alert-row"><div><div class="alert-model">fraud-detector-v3</div><div class="alert-detail">PSI = 0.06 · all features stable</div></div><span class="badge badge-healthy">HEALTHY</span></div>
<div class="alert-row"><div><div class="alert-model">spam-detector-v1</div><div class="alert-detail">PSI = 0.34 · severe drift detected</div></div><span class="badge badge-critical">CRITICAL</span></div>
<div class="alert-row"><div><div class="alert-model">click-predictor-v2</div><div class="alert-detail">PSI = 0.18 · monitoring closely</div></div><span class="badge badge-watch">WATCH</span></div>"""

        st.markdown(f"""
<div class="card">
  <div class="card-title">Recent Analytical Alerts</div>
  <div style="margin-top:10px;">{alerts_html}</div>
</div>""", unsafe_allow_html=True)

        # EventBridge
        st.markdown("""
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <div class="card-title">AWS EventBridge Schedule</div>
      <div style="color:#8b949e;font-size:0.75rem;margin-top:2px;font-family:monospace;">rate(1 hour) · drift-detector-rule</div>
    </div>
    <span class="badge badge-active">● ACTIVE</span>
  </div>
</div>""", unsafe_allow_html=True)

        # Step Functions
        st.markdown("""
<div class="card">
  <div class="card-title">Escalation Workflow</div>
  <div class="card-sub">AWS Step Functions</div>
  <div class="step-row">
    <div class="step-num blue">1</div>
    <div><div class="step-title">Check Drift</div><div class="step-sub">PSI computation on recent window</div></div>
  </div>
  <div class="step-row">
    <div class="step-num green">2</div>
    <div><div class="step-title">Evaluate State</div><div class="step-sub">Severity classification</div></div>
  </div>
  <div class="step-row">
    <div class="step-num yellow">3</div>
    <div><div class="step-title">Escalate Alert via SNS</div><div class="step-sub">Notify owners · alert email</div></div>
  </div>
  <div class="step-row">
    <div class="step-num red">4</div>
    <div><div class="step-title">Wait &amp; Recheck</div><div class="step-sub">Loop until drift resolves</div></div>
  </div>
</div>""", unsafe_allow_html=True)

        # Kinesis
        st.markdown("""
<div class="card" style="padding-bottom:0">
  <div class="card-title">Kinesis High-Volume Ingestion</div>
  <div class="card-sub">ml-predictions-stream · 1 shard</div>
  <div class="kinesis-metrics">
    <div class="km-cell"><div class="km-val">API</div><div class="km-label">Ingestion Path</div></div>
    <div class="km-cell"><div class="km-val">100</div><div class="km-label">Batch Size</div></div>
    <div class="km-cell"><div class="km-val">24h</div><div class="km-label">Retention</div></div>
  </div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# TAB 3 — CONFIGURE
# ══════════════════════════════════════════════════════
with t3:
    cl, cr = st.columns([1, 1], gap="large")

    with cl:
        st.markdown('<div class="card-title" style="margin-bottom:2px;">Per-Model Drift Thresholds Manager</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-sub" style="margin-bottom:12px;">Applied immediately to new detection windows</div>', unsafe_allow_html=True)

        with st.form("cfg_form"):
            st.markdown('<div class="sec-label">TARGET MODEL</div>', unsafe_allow_html=True)
            cfg_model = st.selectbox("", ["spam-detector-v1", "fraud-detector-v3",
                                           "click-predictor-v2", "recommendation-engine-v4"],
                                     label_visibility="collapsed")
            st.markdown('<div class="sec-label">CONFIDENCE THRESHOLD</div>', unsafe_allow_html=True)
            conf_t = st.slider("", 0.0, 1.0, 0.75, 0.01, label_visibility="collapsed", key="cfg_conf")
            st.markdown(f'<div style="color:#8b949e;font-size:0.75rem;margin-bottom:8px;">Predictions below {conf_t:.2f} flagged as low-confidence</div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-label">PSI THRESHOLD</div>', unsafe_allow_html=True)
            psi_t = st.slider("", 0.05, 0.5, 0.20, 0.01, label_visibility="collapsed", key="cfg_psi")
            st.markdown(f'<div style="color:#8b949e;font-size:0.75rem;margin-bottom:8px;">Drift alert fires when PSI ≥ {psi_t:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-label">OWNER NOTIFICATION EMAIL</div>', unsafe_allow_html=True)
            owner = st.text_input("", placeholder="mansican908@gmail.com", label_visibility="collapsed")
            st.markdown('<div class="sec-label">DESCRIPTION</div>', unsafe_allow_html=True)
            desc  = st.text_input("", placeholder="Short description of this configuration", label_visibility="collapsed", key="cfg_desc")
            saved = st.form_submit_button("Save Configuration", use_container_width=True)

        if saved:
            res, code = api_post(f"/models/{cfg_model}/config", {
                "confidence_threshold": conf_t, "psi_threshold": psi_t,
                "owner_email": owner or "mansican908@gmail.com", "description": desc,
            })
            st.success(f"Config saved for {cfg_model}")

        # Fetch config
        st.markdown('<div class="chart-hdr" style="margin-top:18px;"><div class="chart-hdr-title">Active Threshold Fetcher</div><div class="chart-hdr-sub">Live values from DynamoDB</div></div>',
                    unsafe_allow_html=True)
        fc1, fc2 = st.columns([2, 1])
        with fc1:
            fetch_model = st.selectbox("", ["spam-detector-v1", "fraud-detector-v3",
                                             "click-predictor-v2", "recommendation-engine-v4"],
                                       label_visibility="collapsed", key="fmod")
        with fc2:
            st.markdown('<div id="fetch-btn-marker"></div>', unsafe_allow_html=True)
            fetch_btn = st.button("Fetch Config", use_container_width=True, key="fetch_btn")
        if fetch_btn:
            cfg, code = api_get(f"/models/{fetch_model}/config")
            if code == 200 and "error" not in cfg:
                m1, m2 = st.columns(2)
                m1.markdown(f"""
<div style="background:#0a0a0a;border:1px solid #262626;border-radius:8px;padding:12px;text-align:center;">
  <div style="color:#8b949e;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;">CONFIDENCE LIMIT</div>
  <div style="color:#f5f5f5;font-size:1.4rem;font-weight:700;margin:4px 0;">{cfg.get('confidence_threshold','—')}</div>
</div>""", unsafe_allow_html=True)
                m2.markdown(f"""
<div style="background:#0a0a0a;border:1px solid #262626;border-radius:8px;padding:12px;text-align:center;">
  <div style="color:#8b949e;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;">PSI LIMIT</div>
  <div style="color:#f5f5f5;font-size:1.4rem;font-weight:700;margin:4px 0;">{cfg.get('psi_threshold','—')}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#8b949e;font-size:0.82rem;">No custom config — using defaults (0.75 / 0.20)</div>', unsafe_allow_html=True)

    with cr:
        # Ground truth accuracy matrix
        st.markdown('<div class="chart-hdr"><div class="chart-hdr-title">Ground Truth Accuracy Matrix</div></div>',
                    unsafe_allow_html=True)
        if gt_items:
            gt_df2 = pd.DataFrame(gt_items)
            by_model = gt_df2.groupby("model_id").apply(
                lambda g: sum(1 for r in g["correct"] if r) / len(g)
            ).reset_index()
            by_model.columns = ["model", "accuracy"]
            fig_acc = go.Figure(go.Bar(
                x=by_model["model"], y=by_model["accuracy"],
                marker_color=[conf_color(v) for v in by_model["accuracy"]],
                marker_line_width=0,
            ))
            fig_acc.add_hline(y=0.9, line_dash="dash", line_color="#8b949e", line_width=1,
                              annotation_text="Target: 0.90", annotation_font_color="#8b949e")
            fig_acc.update_layout(**CHART_CARD, height=200, yaxis_range=[0, 1], yaxis_tickformat=".0%")
            st.plotly_chart(fig_acc, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div style="color:#8b949e;font-size:0.82rem;padding:12px 0 20px;">No ground truth labels submitted yet.</div>',
                        unsafe_allow_html=True)

        # Ground truth records table
        st.markdown('<div class="chart-hdr" style="margin-top:8px;"><div class="chart-hdr-title">Ground Truth Records</div></div>',
                    unsafe_allow_html=True)
        if gt_items:
            gt_rows = ""
            for g in gt_items:
                match = g.get("correct", False)
                result_badge = (
                    '<span class="conf-badge conf-green">MATCH</span>'
                    if match else
                    '<span class="conf-badge conf-red">MISMATCH</span>'
                )
                gt_rows += (
                    f"<tr>"
                    f"<td><span style='color:#14b8a6;font-weight:600'>{g.get('model_id','')}</span></td>"
                    f"<td>{g.get('predicted','')}</td>"
                    f"<td>{g.get('actual','')}</td>"
                    f"<td>{result_badge}</td>"
                    f"</tr>"
                )
            st.markdown(f"""
<div style="background:#0a0a0a;border:1px solid #262626;border-radius:10px;overflow:hidden;margin-bottom:12px;">
<table class="pred-table">
  <thead><tr>
    <th>MODEL</th><th>PREDICTED</th><th>ACTUAL</th><th>RESULT</th>
  </tr></thead>
  <tbody>{gt_rows}</tbody>
</table>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#8b949e;font-size:0.82rem;padding-bottom:12px;">Submit ground truth labels in the Drift Control tab.</div>',
                        unsafe_allow_html=True)

        # Daily report
        st.markdown("""
<div class="card" style="margin-top:8px;">
  <div class="card-title">Automated Daily Audit Report</div>
  <div class="card-sub">Aggregates the last 24h · saved to S3</div>
</div>""", unsafe_allow_html=True)
        if st.button("Generate 24h Report", use_container_width=True, key="gen_report"):
            st.info("Report generation requires refreshed AWS credentials. The Lambda runs automatically at midnight via EventBridge.")

# ══════════════════════════════════════════════════════
# TAB 4 — SIMULATE DRIFT
# ══════════════════════════════════════════════════════
with t4:
    SCENARIOS = {
        "Gradual Spam Pattern Shift": [
            ("Stable",       0.85, 0.95, 10, "p1", "P1"),
            ("Early Drift",  0.70, 0.85, 10, "p2", "P2"),
            ("Mid Drift",    0.55, 0.70, 10, "p3", "P3"),
            ("Severe Drift", 0.30, 0.55, 10, "p4", "P4"),
        ],
        "Sudden Model Collapse": [
            ("Stable", 0.88, 0.97, 6, "p1", "P1"),
            ("Crash",  0.20, 0.50, 14, "p4", "P4"),
        ],
        "Recovery After Retraining": [
            ("Drifting",   0.40, 0.62, 8, "p4", "P4"),
            ("Recovering", 0.65, 0.80, 8, "p2", "P2"),
            ("Stable",     0.88, 0.97, 8, "p1", "P1"),
        ],
        "Healthy Baseline": [
            ("Stable", 0.88, 0.97, 15, "p1", "P1"),
        ],
    }

    # Controls row
    sc1, sc2, sc3 = st.columns([2, 2, 1], gap="small")
    with sc1:
        st.markdown('<div class="sec-label">SCENARIO</div>', unsafe_allow_html=True)
        sk = st.selectbox("", list(SCENARIOS.keys()), label_visibility="collapsed")
    with sc2:
        st.markdown('<div class="sec-label">TARGET MODEL</div>', unsafe_allow_html=True)
        sim_model = st.selectbox("", ["spam-detector-v1", "fraud-detector-v3",
                                       "click-predictor-v2", "recommendation-engine-v4"],
                                 label_visibility="collapsed", key="sim_model")
    with sc3:
        st.markdown('<div class="sec-label">INTER-EVENT DELAY (MS)</div>', unsafe_allow_html=True)
        delay_ms = st.slider("", 20, 500, 100, 10, label_visibility="collapsed")

    phases = SCENARIOS[sk]
    total_count = sum(p[3] for p in phases)

    # Phase cards
    _pc_cls = {"p1": "pc-green", "p2": "pc-yellow", "p3": "pc-orange", "p4": "pc-red"}
    ph_cols = st.columns(len(phases), gap="small")
    for i, (ph_name, lo, hi, cnt, badge_cls, badge_lbl) in enumerate(phases):
        ph_cols[i].markdown(f"""
<div class="phase-card {_pc_cls.get(badge_cls, '')}">
  <div class="phase-header">
    <div class="phase-name">{ph_name}</div>
    <div class="phase-badge {badge_cls}">{badge_lbl}</div>
  </div>
  <div class="phase-row"><span class="phase-lbl">Confidence range</span></div>
  <div class="phase-row"><span class="phase-val">{lo:.2f} – {hi:.2f}</span></div>
  <div class="phase-row" style="margin-top:6px"><span class="phase-lbl">Predictions</span></div>
  <div class="phase-row"><span class="phase-val">{cnt}</span></div>
</div>""", unsafe_allow_html=True)

    # Run + Reset buttons
    rb1, rb2 = st.columns([4, 1], gap="small")
    with rb1:
        run = st.button(f"⚡ Run Simulation", type="primary", use_container_width=True)
    with rb2:
        st.markdown('<div id="reset-btn-marker"></div>', unsafe_allow_html=True)
        if st.button("↺ Reset", use_container_width=True, key="reset_sim"):
            st.session_state.predictions = []
            st.rerun()

    # Progress + status
    prog_ph   = st.empty()
    status_ph = st.empty()

    def _prog_html(done, total):
        pct = (done / total * 100) if total else 0
        return f"""
<div style="background:#171717;border:1px solid #262626;border-radius:12px;
  padding:14px 18px;margin:8px 0 4px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
    <span style="color:#f5f5f5;font-size:0.82rem;font-weight:600;font-family:'JetBrains Mono',monospace;">
      Predictions Sent:&nbsp;<span style="color:#14b8a6;">{done}</span>&nbsp;/&nbsp;{total}
    </span>
    <span style="color:#737373;font-size:0.78rem;">{pct:.1f}% Completed</span>
  </div>
  <div style="background:#262626;border-radius:9999px;height:6px;width:100%;overflow:hidden;">
    <div style="background:#14b8a6;height:6px;border-radius:9999px;
      width:{pct:.2f}%;transition:width 0.3s ease-out;"></div>
  </div>
</div>"""

    # Live chart + log side by side
    chart_col, log_col = st.columns([3, 2], gap="small")

    with chart_col:
        st.markdown("""
<div style="background:#171717;border:1px solid #262626;border-radius:10px;padding:14px 16px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
    <span style="color:#14b8a6;font-size:0.85rem;">📈</span>
    <span style="color:#f5f5f5;font-size:0.85rem;font-weight:600;">Live Confidence Scatter</span>
  </div>
  <div style="color:#8b949e;font-size:0.75rem;margin-bottom:8px;">Streamed from simulation</div>
""", unsafe_allow_html=True)
        chart_ph = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)

    with log_col:
        st.markdown("""
<div style="background:#171717;border:1px solid #262626;border-radius:10px;padding:14px 16px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
    <span style="color:#2dd4bf;font-size:0.85rem;">📋</span>
    <span style="color:#f5f5f5;font-size:0.85rem;font-weight:600;">Simulation Log</span>
  </div>
""", unsafe_allow_html=True)
        log_ph2 = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)

    if run:
        labels = ["spam", "ham"] if "spam" in sim_model else \
                 ["fraud", "legit"] if "fraud" in sim_model else \
                 ["click", "no-click"] if "click" in sim_model else ["rec", "no-rec"]

        sent  = []
        done  = 0
        logs  = ["Awaiting simulation start…"]
        prog_ph.markdown(_prog_html(0, total_count), unsafe_allow_html=True)

        phase_colors = {"p1": "#3fb950", "p2": "#d29922", "p3": "#e06c00", "p4": "#f85149"}

        for ph_name, lo, hi, cnt, badge_cls, badge_lbl in phases:
            col = phase_colors[badge_cls]
            status_ph.markdown(
                f'<div class="status-line">Current phase: <strong>{ph_name}</strong> · confidence {lo:.2f}–{hi:.2f}</div>',
                unsafe_allow_html=True
            )
            logs = [f"━━ Phase: {ph_name} ({lo:.2f}–{hi:.2f}) ━━"]

            for _ in range(cnt):
                conf  = round(random.uniform(lo, hi), 3)
                lbl   = random.choice(labels)
                res, code = api_post("/predictions", {
                    "model_id": sim_model, "prediction": lbl, "confidence": conf
                })
                if code == 200:
                    st.session_state.predictions.append({
                        "id": res["id"], "model_id": sim_model,
                        "prediction": lbl, "confidence": conf,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    sent.append({"phase": ph_name, "confidence": conf, "i": done, "color": col})
                    icon = "✓" if conf >= 0.75 else "⚠"
                    logs.append(f"  {icon}  conf={conf:.3f}  label={lbl}")
                else:
                    logs.append(f"  ✗  error: {res}")

                done += 1
                prog_ph.markdown(_prog_html(done, total_count), unsafe_allow_html=True)
                log_lines_html = "".join(
                    f'<div style="color:{"#3fb950" if "✓" in l else "#f85149" if "✗" in l else "#d29922" if "━━" in l else "#737373"};'
                    f'font-size:0.76rem;line-height:1.7;white-space:pre;">{l}</div>'
                    for l in logs[-18:]
                )
                log_ph2.markdown(
                    f'<div style="background:#0a0a0a;border-radius:6px;padding:10px 12px;'
                    f'font-family:monospace;max-height:260px;overflow-y:auto;">'
                    f'{log_lines_html}</div>',
                    unsafe_allow_html=True
                )

                if sent and done % 3 == 0:
                    mini = pd.DataFrame(sent)
                    fig_s = go.Figure()
                    for ph, grp in mini.groupby("phase"):
                        c = grp["color"].iloc[0]
                        fig_s.add_trace(go.Scatter(
                            x=grp["i"], y=grp["confidence"], mode="markers",
                            name=ph, marker=dict(color=c, size=7, opacity=0.85),
                        ))
                    fig_s.add_hline(y=0.75, line_dash="dash", line_color="#d29922", line_width=1.5)
                    fig_s.update_layout(**CHART, height=280, yaxis_range=[0, 1.05],
                                        xaxis_title="Prediction #", yaxis_title="Confidence",
                                        legend=dict(bgcolor="rgba(0,0,0,0)", font_color="#8b949e",
                                                    orientation="h", y=1.08))
                    chart_ph.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})

                time.sleep(delay_ms / 1000)

        status_ph.markdown(
            '<div class="status-line">✅  Predictions sent — running drift detection automatically…</div>',
            unsafe_allow_html=True
        )

        # Auto-trigger drift detection after simulation
        try:
            _lambda = boto3.client('lambda', region_name='us-east-1')
            resp = _lambda.invoke(
                FunctionName='ml-drift-detector',
                InvocationType='RequestResponse',
                Payload=b'{}'
            )
            result = json.loads(resp['Payload'].read())
            body = json.loads(result.get('body', '{}'))
            alerts = body.get('alerts_fired', [])
            models = body.get('models_checked', [])
            checked = body.get('predictions_total', 0)

            if alerts:
                status_ph.markdown(
                    f'<div class="status-line" style="border-color:#da3633;">'
                    f'⚠ Drift detected on <strong style="color:#f85149">{", ".join(alerts)}</strong> '
                    f'· SNS alert fired · Step Functions started · '
                    f'<strong>check your email + switch to Live Monitor</strong></div>',
                    unsafe_allow_html=True
                )
                st.session_state.drift_alerts = [
                    {"model": m, "detail": "Drift detected by simulation run", "critical": True}
                    for m in alerts
                ]
            else:
                status_ph.markdown(
                    f'<div class="status-line" style="border-color:#238636;">'
                    f'✅ No drift detected across {len(models)} model(s) · {checked} predictions analyzed'
                    f'</div>',
                    unsafe_allow_html=True
                )
        except Exception as e:
            status_ph.markdown(
                f'<div class="status-line">✅ Simulation complete — '
                f'<strong>switch to Live Monitor</strong> to see charts '
                f'(drift detector: {str(e)[:60]})</div>',
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════
# TAB 5 — LIVE CLASSIFIER
# ══════════════════════════════════════════════════════

@st.cache_resource
def load_spam_model():
    model_path = os.path.join(os.path.dirname(__file__), "models", "spam_classifier.pkl")
    if not os.path.exists(model_path):
        return None
    with open(model_path, "rb") as f:
        return pickle.load(f)

EXAMPLES = {
    "🚨 Obvious spam": "WINNER!! You have been selected to receive a £900 prize reward! Call 09061701461 NOW to claim your prize. T&C apply.",
    "📱 Subtle spam": "You have 1 new message. Call 08719181503 to retrieve your voicemail. Standard rates apply.",
    "✅ Normal message": "Hey, are you coming to the study group tonight? I'll bring the notes from last week.",
    "💬 Casual text": "Can you pick up some milk on your way home? Also, dinner is at 7.",
    "🎁 Borderline offer": "As a valued customer you have been selected to receive our special discount offer this week only.",
}

with t5:
    spam_model = load_spam_model()

    if spam_model is None:
        st.markdown("""
<div class="card" style="text-align:center;padding:40px;">
  <div style="font-size:2rem;margin-bottom:12px;">⚠️</div>
  <div style="color:#f5f5f5;font-weight:600;">Model not found</div>
  <div style="color:#8b949e;font-size:0.85rem;margin-top:6px;">Run <code>python3 train_model.py</code> first</div>
</div>""", unsafe_allow_html=True)
    else:
        # ── Header ──────────────────────────────────────────────────────────
        st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
  <div style="background:linear-gradient(135deg,#238636,#2ea043);border-radius:8px;
    padding:8px 14px;color:#fff;font-size:0.82rem;font-weight:700;letter-spacing:0.04em;">
    REAL MODEL
  </div>
  <div>
    <div style="color:#f5f5f5;font-size:0.95rem;font-weight:600;">TF-IDF + Naive Bayes Spam Classifier</div>
    <div style="color:#8b949e;font-size:0.75rem;">Trained on 5,574 real SMS messages · 98.5% accuracy · predictions flow into the live pipeline</div>
  </div>
</div>""", unsafe_allow_html=True)

        lc_left, lc_right = st.columns([1, 1], gap="large")

        with lc_left:
            st.markdown('<div class="card-title" style="margin-bottom:2px;">Type a Message to Classify</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-sub" style="margin-bottom:14px;">The real model reads the text and gives a confidence score</div>', unsafe_allow_html=True)

            # Example picker
            st.markdown('<div class="sec-label">LOAD AN EXAMPLE</div>', unsafe_allow_html=True)
            example_choice = st.selectbox("", ["— pick an example —"] + list(EXAMPLES.keys()),
                                          label_visibility="collapsed", key="ex_pick")
            default_text = EXAMPLES.get(example_choice, "")

            st.markdown('<div class="sec-label" style="margin-top:10px;">MESSAGE TEXT</div>', unsafe_allow_html=True)
            msg_text = st.text_area("", value=default_text, height=130,
                                    placeholder="Type any message here...",
                                    label_visibility="collapsed", key="msg_input")

            classify_btn = st.button("🔍 Classify Message", use_container_width=True, type="primary")

            # How it works card
            st.markdown("""
<div class="card">
  <div class="card-title">How it works</div>
  <div class="card-sub">Under the hood</div>
  <div style="display:flex;flex-direction:column;gap:8px;">
    <div style="display:flex;gap:10px;align-items:flex-start;">
      <span style="color:#14b8a6;font-weight:700;min-width:20px;">1</span>
      <span style="color:#e5e5e5;font-size:0.82rem;">TF-IDF vectorizer converts text into 10,000 weighted word/bigram features</span>
    </div>
    <div style="display:flex;gap:10px;align-items:flex-start;">
      <span style="color:#14b8a6;font-weight:700;min-width:20px;">2</span>
      <span style="color:#e5e5e5;font-size:0.82rem;">Naive Bayes computes P(spam|words) using Bayes theorem on training frequencies</span>
    </div>
    <div style="display:flex;gap:10px;align-items:flex-start;">
      <span style="color:#14b8a6;font-weight:700;min-width:20px;">3</span>
      <span style="color:#e5e5e5;font-size:0.82rem;">Confidence score (predict_proba) sent to API Gateway → DynamoDB → drift monitor</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        # Run classification and store result in session state so it survives re-runs
        if "lc_result" not in st.session_state:
            st.session_state.lc_result = None

        if classify_btn and msg_text.strip():
            text  = msg_text.strip()
            proba = spam_model.predict_proba([text])[0]
            classes   = list(spam_model.classes_)
            spam_prob = proba[classes.index("spam")]
            ham_prob  = proba[classes.index("ham")]
            is_spam   = spam_prob > 0.5
            confidence = spam_prob if is_spam else ham_prob
            st.session_state.lc_result = {
                "text": text, "spam_prob": spam_prob, "ham_prob": ham_prob,
                "is_spam": is_spam, "confidence": confidence,
                "label": "SPAM" if is_spam else "HAM",
                "sent": False,
            }
        elif classify_btn and not msg_text.strip():
            st.session_state.lc_result = None

        with lc_right:
            res_state = st.session_state.lc_result
            if res_state:
                is_spam    = res_state["is_spam"]
                confidence = res_state["confidence"]
                spam_prob  = res_state["spam_prob"]
                ham_prob   = res_state["ham_prob"]
                result_label  = res_state["label"]
                result_color  = "#f85149" if is_spam else "#3fb950"
                result_bg     = "#2d0f0f" if is_spam else "#0f2d17"
                result_border = "#da3633" if is_spam else "#238636"
                result_icon   = "🚨" if is_spam else "✅"

                st.markdown(f"""
<div style="background:{result_bg};border:2px solid {result_border};border-radius:12px;
  padding:24px;text-align:center;margin-bottom:14px;">
  <div style="font-size:2.5rem;margin-bottom:8px;">{result_icon}</div>
  <div style="color:{result_color};font-size:1.8rem;font-weight:800;letter-spacing:0.1em;">
    {result_label}
  </div>
  <div style="color:#8b949e;font-size:0.8rem;margin-top:4px;">
    Confidence: <strong style="color:{result_color}">{confidence:.1%}</strong>
  </div>
</div>""", unsafe_allow_html=True)

                st.markdown(f"""
<div class="card">
  <div class="card-title">Raw Probabilities</div>
  <div style="margin-top:10px;">
    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
      <span style="color:#f85149;font-size:0.82rem;font-weight:600;">Spam</span>
      <span style="color:#f85149;font-size:0.82rem;">{spam_prob:.1%}</span>
    </div>
    <div style="background:#262626;border-radius:4px;height:8px;margin-bottom:12px;">
      <div style="background:#f85149;height:8px;border-radius:4px;width:{spam_prob*100:.1f}%;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
      <span style="color:#3fb950;font-size:0.82rem;font-weight:600;">Ham</span>
      <span style="color:#3fb950;font-size:0.82rem;">{ham_prob:.1%}</span>
    </div>
    <div style="background:#262626;border-radius:4px;height:8px;">
      <div style="background:#3fb950;height:8px;border-radius:4px;width:{ham_prob*100:.1f}%;"></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

                st.markdown("""
<div class="chart-hdr" style="margin-top:8px;">
  <div class="chart-hdr-title">Send to Monitoring Pipeline</div>
  <div class="chart-hdr-sub">Logs this prediction to DynamoDB via API Gateway</div>
</div>""", unsafe_allow_html=True)

                if res_state.get("sent"):
                    st.success(f"Logged · confidence {confidence:.1%} · switch to Live Monitor to see it on the chart")
                elif st.button("⚡ Send to Pipeline", use_container_width=True, key="send_live"):
                    api_res, code = api_post("/predictions", {
                        "model_id":   "spam-detector-v1",
                        "prediction": result_label.lower(),
                        "confidence": round(float(confidence), 4),
                    })
                    if code == 200:
                        st.session_state.predictions.append({
                            "id":         api_res.get("id", ""),
                            "model_id":   "spam-detector-v1",
                            "prediction": result_label.lower(),
                            "confidence": round(float(confidence), 4),
                            "timestamp":  datetime.utcnow().isoformat(),
                        })
                        st.session_state.lc_result["sent"] = True
                        st.rerun()
                    else:
                        st.error(str(api_res))

            elif classify_btn and not msg_text.strip():
                st.markdown("""
<div style="background:#171717;border:1px solid #262626;border-radius:10px;
  padding:32px;text-align:center;">
  <div style="color:#8b949e;font-size:0.85rem;">Type a message first</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
<div style="background:#0a0a0a;border:1px solid #262626;border-radius:12px;
  padding:52px 28px;text-align:center;border-style:dashed;">
  <div style="font-size:2.4rem;margin-bottom:12px;opacity:0.6;">✉️</div>
  <div style="color:#e5e5e5;font-weight:600;font-size:0.95rem;margin-bottom:6px;">Result appears here</div>
  <div style="color:#484f58;font-size:0.80rem;line-height:1.5;">
    Type or load a message on the left,<br>then click <strong style="color:#8b949e;">Classify Message</strong>
  </div>
</div>""", unsafe_allow_html=True)
