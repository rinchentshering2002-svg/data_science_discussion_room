"""
PRG405 — Discussion Room Booking Analytics Dashboard (v6.0)
Interactive analysis + hypothesis testing + data-quality transparency
+ a "How we analyse" methodology tab with live numbers.

Run:  streamlit run app.py
Privacy: personal identifiers are dropped before any display or export.
"""

import itertools
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import chi2_contingency, chisquare

# ----------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Discussion Room Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Design tokens
# ----------------------------------------------------------------------
NAVY, TEAL, AMBER = "#203746", "#397782", "#C18B52"
SLATE, SAND, MIST = "#526477", "#8795A5", "#A7BEC1"
SERIES = [TEAL, AMBER, SLATE, "#5EAAB0", SAND, "#245B68", "#D9B58A", MIST]
SCALE_TEAL = [[0.0, "#F7FAFA"], [0.25, "#C8DDDE"], [0.5, "#91B9BC"], [0.75, "#477F8A"], [1.0, "#1B3140"]]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MISSING = "Missing / unclear"

px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = SERIES

PLOT_CFG = {"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
            "modeBarButtonsToRemove": ["lasso2d", "select2d"]}

# Version-aware Streamlit helpers (Q5 — wrapped in try/except)
try:
    _NEW_ST = tuple(int(x) for x in st.__version__.split(".")[:2]) >= (1, 49)
except (ValueError, AttributeError):
    _NEW_ST = False

_chart_ids = itertools.count()


def show(fig):
    """Render a Plotly figure full-width (works across Streamlit versions)."""
    key = f"chart_{next(_chart_ids)}"
    if _NEW_ST:
        st.plotly_chart(fig, width="stretch", config=PLOT_CFG, key=key)
    else:
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG, key=key)


def table(data, **kw):
    if _NEW_ST:
        st.dataframe(data, width="stretch", **kw)
    else:
        st.dataframe(data, use_container_width=True, **kw)


# ----------------------------------------------------------------------
# CSS
# ----------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

.stApp { background: #F4F6F8; color: #253746; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
h1,h2,h3,h4,h5,p,li,label,td,th,input,textarea,button,.stMarkdown { font-family: 'Inter', -apple-system, sans-serif; }
.block-container { max-width: 1500px; padding-top: 3.4rem; padding-bottom: 3rem; }
h1,h2,h3,h4,h5 { color: #203746; letter-spacing: -0.02em; }
h2 { font-size: 1.4rem !important; font-weight: 700 !important; }
h3 { font-size: 1.15rem !important; font-weight: 650 !important; }
[data-testid="stCaptionContainer"] p { color: #71808C; font-size: .82rem; }

/* Sidebar */
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#F8FAFB,#EEF3F5); border-right: 1px solid #E1E7EB; }
section[data-testid="stSidebar"] .stButton button { border:1px solid #D6E0E5; background:#fff; color:#203746; border-radius:8px; font-weight:600; transition:.2s; }
section[data-testid="stSidebar"] .stButton button:hover { border-color:#397782; color:#397782; background:#F1F7F7; transform:translateY(-1px); }
[data-testid="stFileUploadDropzone"] > div { display:flex !important; flex-direction:column !important; align-items:center !important; gap:8px !important; padding:1rem !important; }

/* Hero */
.hero { background: linear-gradient(135deg,#1B3140 0%,#203746 45%,#2D5A6B 100%); padding: 1.9rem 2.2rem; border-radius: 16px; color:#fff;
        margin-bottom: 1.1rem; border:1px solid #304C5B; box-shadow:0 8px 28px rgba(32,55,70,.16); position:relative; overflow:hidden; }
.hero::before { content:''; position:absolute; top:-50%; right:-8%; width:480px; height:480px; background:radial-gradient(circle,rgba(94,170,176,.35),transparent 70%); animation: float 12s ease-in-out infinite; }
.hero::after  { content:''; position:absolute; bottom:-65%; left:-5%; width:380px; height:380px; background:radial-gradient(circle,rgba(193,139,82,.20),transparent 70%); animation: float 16s ease-in-out infinite reverse; }
@keyframes float { 0%,100%{transform:translate(0,0) scale(1);} 50%{transform:translate(20px,-18px) scale(1.06);} }
.hero > * { position:relative; z-index:1; }
.hero h1 { margin:0; font-size:1.85rem; font-weight:750; color:#fff; letter-spacing:-.035em; }
.hero p  { margin:.5rem 0 .9rem; max-width:980px; color:#DCE6EB; font-size:.92rem; line-height:1.65; }
.chip { display:inline-block; padding:.28rem .75rem; margin:0 .4rem .3rem 0; border-radius:999px; font-size:.76rem; font-weight:600;
        background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.22); color:#EAF2F3; backdrop-filter: blur(4px); }

/* KPI */
.kpi { background:#fff; border:1px solid #E1E7EB; border-radius:14px; padding:1.1rem 1.2rem; min-height:132px; height:100%;
       box-shadow:0 2px 8px rgba(30,50,65,.04); position:relative; overflow:hidden; transition:.25s; }
.kpi::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,#397782,#5EAAB0 70%,#C18B52); }
.kpi:hover { transform:translateY(-3px); box-shadow:0 12px 28px rgba(32,55,70,.13); border-color:#C8D6DD; }
.kpi .label { color:#71808C; font-family:'JetBrains Mono',monospace; font-size:.66rem; text-transform:uppercase; letter-spacing:.12em; margin-bottom:.6rem; }
.kpi .value { font-size:1.65rem; font-weight:800; line-height:1.2; letter-spacing:-.03em; overflow-wrap:anywhere;
              background:linear-gradient(135deg,#203746 30%,#397782); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.kpi .sub { color:#71808C; font-size:.76rem; margin-top:.45rem; line-height:1.4; }

/* Insight + panels */
.insight { border:1px solid #DDE7E9; border-left:4px solid #397782; padding:.8rem 1.05rem; margin:.5rem 0; background:#fff; border-radius:8px; line-height:1.55; font-size:.91rem; transition:.2s; }
.insight:hover { background:#F7FAFA; border-left-color:#C18B52; transform:translateX(3px); box-shadow:0 3px 12px rgba(32,55,70,.06); }
.summary { background:linear-gradient(135deg,#FFFFFF,#F3F8F8); border:1px solid #D8E5E8; border-radius:14px; padding:1.1rem 1.3rem; margin-bottom:1rem; box-shadow:0 2px 10px rgba(30,50,65,.05); }
.summary h4 { margin:0 0 .45rem; }
.summary p { margin:0; line-height:1.7; font-size:.94rem; color:#34495A; }
.sect { margin: 1.4rem 0 .6rem; }
.sect .t { font-size:1.12rem; font-weight:700; color:#203746; letter-spacing:-.02em; }
.sect .s { font-size:.84rem; color:#71808C; margin-top:.1rem; }

/* Pipeline stepper */
.steps { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.8rem; margin:.4rem 0 1rem; }
.step { background:#fff; border:1px solid #E1E7EB; border-radius:14px; padding:1rem 1.05rem; position:relative; transition:.25s; box-shadow:0 2px 8px rgba(30,50,65,.04); }
.step:hover { transform:translateY(-3px); box-shadow:0 12px 26px rgba(32,55,70,.12); border-color:#B9CFD4; }
.step .n { width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg,#397782,#245B68); color:#fff; font-weight:700; font-size:.8rem; display:flex; align-items:center; justify-content:center; margin-bottom:.55rem; }
.step .h { font-weight:700; font-size:.95rem; color:#203746; margin-bottom:.25rem; }
.step .d { font-size:.8rem; color:#5B6C79; line-height:1.5; }
.step .stat { margin-top:.65rem; padding-top:.5rem; border-top:1px dashed #D6E0E5; font-family:'JetBrains Mono',monospace; font-size:.74rem; color:#397782; font-weight:500; }

/* Tabs */
div[data-testid="stTabs"] { margin-top:1.1rem; }
div[data-testid="stTabs"] button { font-weight:600; font-size:.87rem; color:#647582; padding:.65rem .9rem; transition:.18s; }
div[data-testid="stTabs"] button:hover { color:#397782; background:#F4F8F9; border-radius:6px 6px 0 0; }
div[data-testid="stTabs"] button[aria-selected="true"] { color:#203746; font-weight:700; }

/* Misc */
div[data-testid="stDataFrame"] { border:1px solid #E1E7EB; border-radius:10px; overflow:hidden; box-shadow:0 2px 8px rgba(30,50,65,.04); }
div[data-testid="stExpander"] { border:1px solid #E1E7EB; border-radius:10px; background:#fff; }
div[data-testid="stMetric"] { background:#fff; border:1px solid #E1E7EB; border-radius:12px; padding:.8rem 1rem; box-shadow:0 2px 8px rgba(30,50,65,.04); }
.stDownloadButton button { border-radius:8px; border:1px solid #397782; background:#397782; color:#fff; font-weight:600; min-height:2.6rem; transition:.2s; }
.stDownloadButton button:hover { background:#2D626B; border-color:#2D626B; color:#fff; transform:translateY(-1px); box-shadow:0 6px 16px rgba(57,119,130,.25); }
.pill { display:inline-block; padding:.28rem .72rem; border-radius:6px; font-size:.75rem; font-weight:700; margin-right:.35rem; }
.pill.ok { background:#E7F2EC; color:#286044; } .pill.warn { background:#F8F0DF; color:#89651D; } .pill.bad { background:#F8E9E8; color:#984B46; }
.footer { margin-top:3rem; padding-top:1.2rem; border-top:1px solid #E1E7EB; color:#8795A5; font-size:.76rem; text-align:center; }
@media (max-width:768px){ .block-container{padding:1rem;} .hero{padding:1.2rem;} .hero h1{font-size:1.4rem;} }
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# UI helpers
# ----------------------------------------------------------------------
def kpi(col, label, value, sub="", icon="📌"):
    col.markdown(
        f'<div class="kpi"><div class="label">{icon} {label}</div>'
        f'<div class="value">{value}</div><div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def md_bold(text):
    return re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)


def insight(text):
    st.markdown(f'<div class="insight">{md_bold(text)}</div>', unsafe_allow_html=True)


def section(title, subtitle=""):
    sub = f'<div class="s">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="sect"><div class="t">{title}</div>{sub}</div>', unsafe_allow_html=True)


def style_fig(fig, height=380):
    fig.update_layout(
        height=height, autosize=True,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=58, b=35),
        font=dict(family="Inter, Arial, sans-serif", size=12, color="#435563"),
        title=dict(font=dict(size=16, color=NAVY), x=0.02, xanchor="left"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=11, color="#536574")),
        hoverlabel=dict(bgcolor=NAVY, bordercolor=NAVY, font=dict(color="#FFFFFF", size=12)),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor="#DCE3E8", tickfont=dict(size=11, color="#647582"), zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EDF1F4", showline=False, tickfont=dict(size=11, color="#647582"), zeroline=False)
    return fig


def strength_label(v, kind):
    cuts = (0.1, 0.3, 0.5) if kind == "w" else (0.1, 0.2, 0.3)
    return "negligible" if v < cuts[0] else "small" if v < cuts[1] else "medium" if v < cuts[2] else "large"


# ----------------------------------------------------------------------
# Data loading + privacy + derived features
# ----------------------------------------------------------------------
CANDIDATES = [
    Path("data/processed/discussion_room_bookings_cleaned.csv"),
    Path("../data/processed/discussion_room_bookings_cleaned.csv"),
    Path("discussion_room_bookings_cleaned.csv"),
]
ID_COLS = ["name", "student_id", "mobile_no", "raw_line"]


def _room_label(x):
    if x == MISSING:
        return x
    try:
        return f"Room {int(float(x))}"
    except (ValueError, TypeError):
        return str(x)


def _room_sort_key(label):
    if label == MISSING:
        return 999
    digits = "".join(ch for ch in str(label) if ch.isdigit())
    return int(digits) if digits else 998


@st.cache_data(show_spinner="Loading booking data…")
def load_data(source):
    raw = pd.read_csv(source)
    n_raw_cols = raw.shape[1]
    dropped = [c for c in ID_COLS if c in raw.columns]
    df = raw.drop(columns=dropped)  # PRIVACY: identifiers never leave this function

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["date"] = df["timestamp"].dt.date
    df["year"] = df["timestamp"].dt.year.astype("Int64")
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    df["weekday"] = df["timestamp"].dt.day_name()
    if "hour" not in df.columns:
        df["hour"] = df["timestamp"].dt.hour
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce")

    room = df["room_no"].astype("string").str.strip().replace("", pd.NA).fillna(MISSING)
    df["room_label"] = room.map(_room_label)
    df["purpose_clean"] = df["purpose"].astype("string").str.strip().replace("", pd.NA).fillna(MISSING)

    if {"check_in", "check_out"}.issubset(df.columns):
        df["duration_minutes_calculated"] = (
            pd.to_datetime(df["check_out"], errors="coerce") - pd.to_datetime(df["check_in"], errors="coerce")
        ).dt.total_seconds() / 60
    else:
        df["duration_minutes_calculated"] = np.nan
    df["duration_valid"] = df["duration_minutes_calculated"].between(0, 720, inclusive="both")
    meta = {"dropped": dropped, "n_raw_cols": n_raw_cols}
    return df, meta


with st.sidebar:
    st.markdown("### 📂 Data")
    uploaded = st.file_uploader("Upload cleaned CSV (optional)", type="csv")

path = next((p for p in CANDIDATES if p.exists()), None)
if uploaded is not None:
    df, META = load_data(uploaded)
elif path is not None:
    df, META = load_data(str(path))
else:
    st.error("Clean CSV not found. Place `discussion_room_bookings_cleaned.csv` in `data/processed/` or upload it in the sidebar.")
    st.stop()

# ----------------------------------------------------------------------
# Sidebar filters (presets, reset, safe state)
# ----------------------------------------------------------------------
ALL = {
    "f_room": sorted(df["room_label"].unique().tolist(), key=_room_sort_key),
    "f_purpose": sorted(df["purpose_clean"].unique().tolist()),
    "f_day": [d for d in WEEKDAYS if d in set(df["weekday"].dropna())],
}
valid_ts = df["timestamp"].dropna()
MIN_D = valid_ts.min().date() if len(valid_ts) else date.today()
MAX_D = valid_ts.max().date() if len(valid_ts) else date.today()

# Q4 — rename preset for honesty
PRESETS = ["Full period", "Last 30 days", "Last 90 days", "This month (partial)"]


def apply_preset():
    p = st.session_state.get("preset", "Full period")
    if p == "Last 30 days":
        rng = (max(MIN_D, MAX_D - timedelta(days=29)), MAX_D)
    elif p == "Last 90 days":
        rng = (max(MIN_D, MAX_D - timedelta(days=89)), MAX_D)
    elif p == "This month (partial)":
        rng = (max(MIN_D, MAX_D.replace(day=1)), MAX_D)
    else:
        rng = (MIN_D, MAX_D)
    st.session_state["f_dates"] = rng


def reset_filters():
    for k, v in ALL.items():
        st.session_state[k] = v
    st.session_state["preset"] = "Full period"
    st.session_state["f_dates"] = (MIN_D, MAX_D)
    st.session_state["f_valid_only"] = False


# B1 — safe state check that accepts tuple OR single date
for k, opts in ALL.items():
    st.session_state[k] = [x for x in st.session_state.get(k, opts) if x in opts] or opts

cur = st.session_state.get("f_dates")
if isinstance(cur, (tuple, list)):
    ok = len(cur) >= 1 and all(MIN_D <= c <= MAX_D for c in cur)
elif isinstance(cur, date):
    ok = MIN_D <= cur <= MAX_D
else:
    ok = False
if not ok:
    st.session_state["f_dates"] = (MIN_D, MAX_D)

st.session_state.setdefault("f_valid_only", False)
st.session_state.setdefault("preset", "Full period")

with st.sidebar:
    st.markdown("### 🎛️ Filters")
    st.button("↺ Reset all filters", on_click=reset_filters, use_container_width=True)
    st.selectbox("Quick date range", PRESETS, key="preset", on_change=apply_preset)
    dates = st.date_input("Custom date range", min_value=MIN_D, max_value=MAX_D, key="f_dates")
    # B2 — caption clarifying that presets are shortcuts
    st.caption("Presets fill the date range. You can adjust it manually afterwards.")
    f_room = st.multiselect("Room", ALL["f_room"], key="f_room")
    f_purpose = st.multiselect("Purpose", ALL["f_purpose"], key="f_purpose")
    f_day = st.multiselect("Weekday", ALL["f_day"], key="f_day")
    valid_only = st.toggle("Only records with valid duration", key="f_valid_only",
                           help="Keeps bookings whose duration is between 0 and 12 hours.")
    st.caption("This toggle filters the view only. Flagged-duration counts are always reported against the full dataset.")

if isinstance(dates, (tuple, list)):
    d0, d1 = (dates[0], dates[1]) if len(dates) == 2 else (dates[0], dates[0])
else:
    d0 = d1 = dates

mask = (
    df["room_label"].isin(f_room) & df["purpose_clean"].isin(f_purpose) & df["weekday"].isin(f_day)
    & (df["timestamp"].dt.date.between(d0, d1) | df["timestamp"].isna())
)
if valid_only:
    mask &= df["duration_valid"]
fdf = df[mask].copy()

with st.sidebar:
    st.progress(len(fdf) / max(len(df), 1))
    st.caption(f"**{len(fdf):,}** of **{len(df):,}** records match the filters.")

    # B5 — active-filters caption is preset-aware
    active = [n for n, a, b in [("Room", f_room, ALL["f_room"]),
                                ("Purpose", f_purpose, ALL["f_purpose"]),
                                ("Weekday", f_day, ALL["f_day"])] if len(a) != len(b)]
    preset_active = st.session_state.get("preset", "Full period") != "Full period"
    if (d0, d1) != (MIN_D, MAX_D) and preset_active:
        active.append("Dates")
    if valid_only:
        active.append("Valid-only")
    if active:
        st.caption("Active filters: " + " · ".join(active))

    # M3 — Documentation expander
    with st.expander("📚 Documentation"):
        st.markdown(
            "- **ANALYSIS_REPORT.md** — full analysis report\n"
            "- **PRESENTATION_OUTLINE.md** — slide-by-slide guide\n"
            "- **DATA_DICTIONARY.md** — every column explained\n"
            "- **CLEANING_RULES.md** — what cleaning does\n"
            "- **USER_GUIDE.md** — how to use this dashboard"
        )

    # O1 — Demo script expander
    with st.expander("🎬 4-minute demo script"):
        st.markdown(
            "1. **Overview** — read the executive summary, note Room 7 is busiest and "
            "Self-study is 31.5% of bookings.\n"
            "2. **Rooms × Purposes** — switch heatmap to *Row %*, note Room 7 favours "
            "micro-teaching.\n"
            "3. **Hypothesis tests** — H1 (χ² = 43.87, w = 0.16) and H2 "
            "(χ² = 225.08, V = 0.15). Say *significance ≠ size*.\n"
            "4. **Data quality** — show flagged records and recommendations.\n"
            "5. **Data & export** — click CSV, note identifiers excluded."
        )

# ----------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------
chips = ""
if len(valid_ts):
    chips += f'<span class="chip">📅 {MIN_D:%d %b %Y} → {MAX_D:%d %b %Y}</span>'
chips += (f'<span class="chip">🗃️ {len(df):,} records</span>'
          f'<span class="chip">🏢 {df["room_label"].nunique()} rooms</span>'
          f'<span class="chip">🎯 {df["purpose_clean"].nunique()} purposes</span>'
          f'<span class="chip">🔒 Identifiers removed</span>'
          # O2 — Notebook chip
          f'<span class="chip">📓 Notebook: Discussion_Room_Booking_Analysis.ipynb</span>')
st.markdown(
    '<div class="hero"><h1>📊 Discussion Room Booking Analytics</h1>'
    "<p>Explore demand, timing and purpose patterns, test hypotheses live, and audit data quality. "
    "A booking record is a <b>reservation</b>, not verified occupancy.</p>" + chips + "</div>",
    unsafe_allow_html=True,
)

if fdf.empty:
    st.warning("No records match the current filters. Widen the selection in the sidebar.")
    st.stop()

# ----------------------------------------------------------------------
# Core numbers
# ----------------------------------------------------------------------
valid_dur = fdf.loc[fdf["duration_valid"], "duration_minutes_calculated"].dropna()
room_counts = fdf["room_label"].value_counts()
purpose_counts = fdf["purpose_clean"].value_counts()
known_rooms = room_counts[room_counts.index != MISSING]
known_purposes = purpose_counts[purpose_counts.index != MISSING]
active_days = fdf["date"].nunique()
flagged_total = int((~df["duration_valid"]).sum())

c = st.columns(5)
kpi(c[0], "Total bookings", f"{len(fdf):,}", f"Across {active_days:,} active days", "📅")
kpi(c[1], "Busiest room", known_rooms.idxmax() if len(known_rooms) else "—",
    f"{int(known_rooms.max()):,} bookings" if len(known_rooms) else "", "🏆")
kpi(c[2], "Top purpose", known_purposes.idxmax() if len(known_purposes) else "—",
    f"{known_purposes.max() / len(fdf) * 100:.0f}% of bookings" if len(known_purposes) else "", "🎯")
dur_sub = (f"Mean {valid_dur.mean():.0f} min · valid records only" if len(valid_dur) >= 5
           else f"Small sample (n={len(valid_dur)}) · interpret cautiously" if len(valid_dur) else "No valid durations")
kpi(c[3], "Median duration", f"{valid_dur.median():.0f} min" if len(valid_dur) else "—", dur_sub, "⏱️")
kpi(c[4], "Data validity", f"{fdf['duration_valid'].mean() * 100:.1f}%",
    f"{flagged_total:,} flagged durations in full dataset", "✅")
st.write("")

tabs = st.tabs(["🏠 Overview", "📈 Trends", "🔥 Patterns", "🏢 Rooms × Purposes", "🔍 Room explorer",
                "🧪 Hypothesis tests", "🧭 How we analyse", "🛡️ Data quality", "🗂️ Data & export"])
tab_over, tab_trend, tab_pat, tab_rel, tab_drill, tab_hyp, tab_how, tab_qual, tab_data = tabs

# ======================================================================
# OVERVIEW
# ======================================================================
with tab_over:
    # Executive summary (auto-generated narrative)
    parts = [f"Between <b>{d0:%d %b %Y}</b> and <b>{d1:%d %b %Y}</b> the current selection holds "
             f"<b>{len(fdf):,}</b> bookings over <b>{active_days:,}</b> active days"]
    if len(known_rooms):
        parts.append(f"; <b>{known_rooms.idxmax()}</b> is the most requested room "
                     f"({known_rooms.max() / known_rooms.sum() * 100:.0f}% of bookings with a known room)")
    if len(known_purposes):
        parts.append(f" and <b>{known_purposes.idxmax()}</b> the most common purpose")
    if len(valid_dur):
        parts.append(f". Typical (median) booking length is <b>{valid_dur.median():.0f} minutes</b>")
    wd_ = fdf["weekday"].value_counts()
    if len(wd_):
        parts.append(f", and <b>{wd_.idxmax()}</b> is the busiest weekday")
    st.markdown('<div class="summary"><h4>📝 Executive summary</h4><p>' + "".join(parts) + ".</p></div>",
                unsafe_allow_html=True)

    ctrl1, ctrl2 = st.columns(2)
    max_n = min(15, len(purpose_counts))
    if max_n >= 4:
        top_n = ctrl1.slider("Show top N purposes", 3, max_n, min(8, max_n))
    else:
        top_n = max_n
        ctrl1.caption(f"Showing all {max_n} purpose(s) in the current selection.")
    share_mode = ctrl2.radio("Room chart shows", ["Bookings", "Share of total (%)"], horizontal=True)

    a, b = st.columns(2)
    with a:
        room_order = sorted(fdf["room_label"].unique().tolist(), key=_room_sort_key)
        rc = fdf["room_label"].value_counts().reindex(room_order).fillna(0)
        vals = rc if share_mode == "Bookings" else (rc / rc.sum() * 100).round(1)
        fig = px.bar(x=rc.index, y=vals.values, text=vals.values, labels={"x": "Room", "y": share_mode},
                     title="Bookings by room")
        fig.add_hline(y=vals.mean(), line_dash="dash", line_color=AMBER,
                      annotation_text=f"Average ({vals.mean():.0f})", annotation_font_color=AMBER)
        fig.update_traces(textposition="outside", marker_color=TEAL, marker_line_color="#F4F6F8", marker_line_width=2)
        show(style_fig(fig))
    with b:
        pc = purpose_counts.head(top_n).sort_values()
        fig = px.bar(x=pc.values, y=pc.index, orientation="h", text=pc.values,
                     labels={"x": "Bookings", "y": "Purpose"}, title=f"Top {top_n} purposes")
        fig.update_traces(textposition="outside", marker_color=AMBER, marker_line_color="#F4F6F8", marker_line_width=2)
        show(style_fig(fig))

    d_, e_ = st.columns(2)
    with d_:
        top_pc = purpose_counts.head(top_n)
        fig = px.pie(values=top_pc.values, names=top_pc.index, hole=0.6, title="Purpose mix")
        fig.update_traces(textinfo="percent", hovertemplate="%{label}: %{value} bookings<extra></extra>",
                          marker=dict(colors=SERIES, line=dict(color="#F4F6F8", width=3)))
        fig.update_layout(legend=dict(orientation="v", y=0.5, x=1.02))
        show(style_fig(fig))
    with e_:
        if len(valid_dur):
            fig = px.histogram(valid_dur, nbins=30, title="Booking duration distribution",
                               labels={"value": "Minutes", "count": "Bookings"})
            fig.update_traces(marker_color=SLATE, marker_line_color="#F4F6F8", marker_line_width=1.5, opacity=0.9)
            fig.add_vline(x=valid_dur.median(), line_dash="dash", line_color=AMBER,
                          annotation_text=f"Median {valid_dur.median():.0f} min", annotation_position="top right",
                          annotation_font_color=AMBER)
            fig.update_layout(showlegend=False, yaxis_title="Bookings", bargap=0.05)
            show(style_fig(fig))
        else:
            st.info("No valid durations under the current filters.")

    section("Key insights", "Generated from the filtered data — they update as you change filters.")
    if len(known_purposes) >= 2:
        t2 = known_purposes.head(2)
        insight(f"**{t2.index[0]}** and **{t2.index[1]}** together make up **{t2.sum() / len(fdf) * 100:.0f}%** of filtered bookings.")
    if len(known_rooms) >= 2:
        insight(f"**{known_rooms.idxmax()}** is booked **{known_rooms.max() / max(known_rooms.min(), 1):.1f}×** as often as "
                f"**{known_rooms.idxmin()}**, the least-used room.")
    if len(wd_):
        insight(f"Peak weekday is **{wd_.idxmax()}** ({wd_.max():,} bookings); quietest is **{wd_.idxmin()}** ({wd_.min():,}).")
    hr_ = fdf["hour"].dropna().astype(int).value_counts()
    if len(hr_):
        insight(f"Most bookings are submitted around **{hr_.idxmax():02d}:00** (submission time, not room-use time).")

# ======================================================================
# TRENDS
# ======================================================================
with tab_trend:
    t1, t2, t3, t4 = st.columns(4)
    gran = t1.radio("Granularity", ["Daily", "Weekly", "Monthly"], index=2, horizontal=True)
    split = t2.selectbox("Split by", ["None", "Room", "Purpose"])
    cumulative = t3.toggle("Cumulative view", value=False)
    anomalies = t4.toggle("Flag unusual periods (±2σ)", value=True,
                          help="Marks periods whose booking count is more than 2 standard deviations from the mean. Only for 'Split by: None'.")
    freq = {"Daily": "D", "Weekly": "W", "Monthly": "MS"}[gran]
    smooth = st.slider("Rolling average window (periods)", 1, 12, 1, help="1 = no smoothing") if gran != "Monthly" else 1

    ts = fdf.dropna(subset=["timestamp"]).set_index("timestamp")
    if ts.empty:
        st.info("No timestamped records under the current filters.")
    else:
        if split == "None":
            series = ts.resample(freq).size().rename("Bookings").to_frame()
            series["Group"] = "All bookings"
        else:
            col = "room_label" if split == "Room" else "purpose_clean"
            keep = ts[col].value_counts().head(6).index
            series = (ts[ts[col].isin(keep)].groupby(col).resample(freq).size().rename("Bookings")
                      .reset_index().rename(columns={col: "Group"}).set_index("timestamp"))
        series = series.reset_index().rename(columns={"index": "timestamp"}).sort_values(["Group", "timestamp"])
        raw_counts = series["Bookings"].copy()
        if smooth > 1:
            series["Bookings"] = series.groupby("Group")["Bookings"].transform(lambda s: s.rolling(smooth, min_periods=1).mean())
        if cumulative:
            series["Bookings"] = series.groupby("Group")["Bookings"].cumsum()

        fig = px.line(series, x="timestamp", y="Bookings", color="Group", markers=gran != "Daily",
                      title=f"{gran} booking trend" + (" (cumulative)" if cumulative else ""), labels={"timestamp": "Date"})
        fig.update_traces(line=dict(width=2.6, shape="spline"))
        if split == "None":
            fig.update_traces(fill="tozeroy", fillcolor="rgba(57,119,130,0.12)")
            if anomalies and not cumulative and len(raw_counts) >= 6 and raw_counts.std() > 0:
                z = (raw_counts - raw_counts.mean()) / raw_counts.std()
                flag = series[(z.abs() > 2).to_numpy()]
                if len(flag):
                    fig.add_trace(go.Scatter(x=flag["timestamp"], y=flag["Bookings"], mode="markers", name="Unusual (±2σ)",
                                             marker=dict(size=12, color=AMBER, line=dict(color="#fff", width=2), symbol="diamond"),
                                             hovertemplate="%{x|%d %b %Y}<br>%{y:.0f} bookings<extra>Unusual</extra>"))
        fig.update_xaxes(rangeslider_visible=True, rangeslider_thickness=0.06)
        fig.update_layout(hovermode="x unified")
        show(style_fig(fig, 470))
        st.caption("Gaps (e.g. academic breaks) are not necessarily evidence of lower demand.")

    w1, w2 = st.columns(2)
    with w1:
        wc = fdf["weekday"].value_counts().reindex(WEEKDAYS).fillna(0)
        fig = px.bar(x=wc.index, y=wc.values, text=wc.values.astype(int), labels={"x": "Weekday", "y": "Bookings"},
                     title="Bookings by weekday")
        fig.update_traces(textposition="outside", marker_color=TEAL, marker_line_color="#F4F6F8", marker_line_width=2)
        show(style_fig(fig))
    with w2:
        hc = fdf["hour"].dropna().astype(int).value_counts().sort_index()
        fig = px.bar(x=hc.index, y=hc.values, labels={"x": "Submission hour", "y": "Bookings"},
                     title="Bookings by submission hour")
        fig.update_traces(marker_color=AMBER, marker_line_color="#F4F6F8", marker_line_width=2)
        show(style_fig(fig))
        st.caption("Submission hour ≠ room-use hour.")

# ======================================================================
# PATTERNS
# ======================================================================
with tab_pat:
    section("When is demand highest?", "Based on submission time of each booking.")
    hm_data = fdf.dropna(subset=["hour", "weekday"]).copy()
    hm_data["hour"] = hm_data["hour"].astype(int)
    hm = pd.crosstab(hm_data["weekday"], hm_data["hour"]).reindex(WEEKDAYS).fillna(0)
    if hm.size:
        fig = px.imshow(hm, aspect="auto", text_auto=True, color_continuous_scale=SCALE_TEAL,
                        labels={"x": "Submission hour", "y": "Weekday", "color": "Bookings"}, title="Weekday × hour heatmap")
        fig.update_traces(textfont=dict(size=11), hovertemplate="<b>%{y} @ %{x}:00</b><br>%{z} bookings<extra></extra>")
        show(style_fig(fig, 420))

        # Q3 — deterministic stack ordering
        flat_hm = hm.stack(future_stack=True).sort_values(ascending=False).head(5)
        st.markdown("**🔝 Top 5 peak slots**")
        peak = pd.DataFrame({"Slot": [f"{d} · {int(h):02d}:00" for d, h in flat_hm.index],
                             "Bookings": flat_hm.values.astype(int),
                             "Share of selection %": (flat_hm.values / len(fdf) * 100).round(1)})
        table(peak, hide_index=True)

    p1, p2 = st.columns(2)
    vd = fdf[fdf["duration_valid"]]
    with p1:
        if len(vd):
            fig = px.box(vd, x="room_label", y="duration_minutes_calculated", points=False,
                         category_orders={"room_label": sorted(vd["room_label"].unique(), key=_room_sort_key)},
                         labels={"room_label": "Room", "duration_minutes_calculated": "Minutes"},
                         title="Duration by room (valid records)")
            fig.update_traces(marker_color=TEAL, line_color=TEAL)
            show(style_fig(fig))
    with p2:
        if len(vd):
            top_p = vd["purpose_clean"].value_counts().head(6).index
            fig = px.box(vd[vd["purpose_clean"].isin(top_p)], x="purpose_clean", y="duration_minutes_calculated", points=False,
                         labels={"purpose_clean": "Purpose", "duration_minutes_calculated": "Minutes"},
                         title="Duration by purpose (top 6)")
            fig.update_traces(marker_color=AMBER, line_color=AMBER)
            show(style_fig(fig))

    section("Room scorecard")
    sc = fdf.groupby("room_label").agg(Bookings=("room_label", "size"), Valid_pct=("duration_valid", lambda s: s.mean() * 100))
    sc["Median_duration_min"] = vd.groupby("room_label")["duration_minutes_calculated"].median()
    sc = sc.sort_values("Bookings", ascending=False)
    sc["Share_%"] = sc["Bookings"] / sc["Bookings"].sum() * 100
    table(sc.round(1), column_config={
        "Bookings": st.column_config.ProgressColumn("Bookings", min_value=0, max_value=int(sc["Bookings"].max()), format="%d"),
        "Median_duration_min": st.column_config.NumberColumn("Median duration (min)", format="%.0f"),
        "Valid_pct": st.column_config.NumberColumn("Valid %", format="%.1f%%"),
        "Share_%": st.column_config.NumberColumn("Share %", format="%.1f%%"),
    })

# ======================================================================
# ROOMS × PURPOSES
# ======================================================================
with tab_rel:
    ct = pd.crosstab(fdf["room_label"], fdf["purpose_clean"])
    ct = ct.reindex(sorted(ct.index, key=_room_sort_key))
    if ct.size:
        view = st.radio("Heatmap values", ["Counts", "Row % (each room's purpose mix)", "Column % (where each purpose is booked)"],
                        horizontal=True)
        if view == "Counts":
            data, fmt = ct, ".0f"
        elif view.startswith("Row"):
            data, fmt = ct.div(ct.sum(axis=1), axis=0) * 100, ".1f"
        else:
            data, fmt = ct.div(ct.sum(axis=0), axis=1) * 100, ".1f"
        fig = px.imshow(data, text_auto=fmt, aspect="auto",
                        color_continuous_scale=["#F0F5F5", "#D5E5E6", "#A8C9CB", "#75A6AA", "#477F8A", "#245B68"],
                        labels={"x": "Purpose", "y": "Room", "color": view.split(" ")[0]}, title=f"Room × Purpose — {view}")
        fig.update_traces(textfont=dict(size=10))
        show(style_fig(fig, 480))

        stacked = ct.reset_index().melt(id_vars="room_label", var_name="Purpose", value_name="Bookings")
        fig = px.bar(stacked, x="room_label", y="Bookings", color="Purpose", labels={"room_label": "Room"},
                     title="Purpose composition per room")
        show(style_fig(fig, 420))
    else:
        st.info("Not enough data for a cross-tab.")

# ======================================================================
# ROOM EXPLORER (drill-down)
# ======================================================================
with tab_drill:
    section("Room explorer", "Pick a room to compare its profile against all rooms in the current selection.")
    room_opts = sorted(known_rooms.index.tolist(), key=_room_sort_key)
    if not room_opts:
        st.info("No rooms with a known label under the current filters.")
    else:
        sel = st.selectbox("Room", room_opts)
        rd = fdf[fdf["room_label"] == sel]
        rvd = rd.loc[rd["duration_valid"], "duration_minutes_calculated"].dropna()
        rank = int(known_rooms.rank(ascending=False, method="min")[sel])
        share = len(rd) / len(fdf) * 100
        rt = rd["purpose_clean"].value_counts()
        k = st.columns(4)
        kpi(k[0], "Bookings", f"{len(rd):,}", f"{share:.1f}% of selection", "📅")
        kpi(k[1], "Popularity rank", f"#{rank} of {len(known_rooms)}", "by booking count", "🏅")
        kpi(k[2], "Top purpose", rt.idxmax() if len(rt) else "—", f"{rt.max() / len(rd) * 100:.0f}% of this room" if len(rt) else "", "🎯")
        kpi(k[3], "Median duration", f"{rvd.median():.0f} min" if len(rvd) else "—",
            f"all rooms: {valid_dur.median():.0f} min" if len(valid_dur) else "", "⏱️")
        st.write("")

        g1, g2 = st.columns(2)
        with g1:
            mix = pd.DataFrame({sel: rt / max(rt.sum(), 1) * 100,
                                "All rooms": purpose_counts / purpose_counts.sum() * 100}).fillna(0)
            mix = mix.sort_values(sel, ascending=False).head(8).reset_index().rename(columns={"index": "Purpose", "purpose_clean": "Purpose"})
            mix = mix.melt(id_vars="Purpose", var_name="Group", value_name="Share %")
            fig = px.bar(mix, x="Purpose", y="Share %", color="Group", barmode="group", title=f"Purpose mix — {sel} vs all rooms",
                         color_discrete_sequence=[TEAL, SAND])
            show(style_fig(fig))
        with g2:
            w_room = rd["weekday"].value_counts().reindex(WEEKDAYS).fillna(0)
            w_all = fdf["weekday"].value_counts().reindex(WEEKDAYS).fillna(0)
            w_all = w_all / max(len(known_rooms), 1)
            fig = go.Figure()
            fig.add_bar(x=WEEKDAYS, y=w_room.values, name=sel, marker_color=TEAL)
            fig.add_scatter(x=WEEKDAYS, y=w_all.values, name="Average room", mode="lines+markers",
                            line=dict(color=AMBER, dash="dash", width=2.5))
            fig.update_layout(title=f"Weekday profile — {sel} vs average room")
            show(style_fig(fig))

        r_ts = rd.dropna(subset=["timestamp"]).groupby("month").size()
        a_ts = fdf.dropna(subset=["timestamp"]).groupby("month").size() / max(len(known_rooms), 1)
        if len(r_ts):
            fig = go.Figure()
            fig.add_scatter(x=r_ts.index, y=r_ts.values, name=sel, mode="lines+markers", line=dict(color=TEAL, width=3, shape="spline"))
            fig.add_scatter(x=a_ts.index, y=a_ts.values, name="Average room", mode="lines", line=dict(color=AMBER, dash="dash", width=2))
            fig.update_layout(title=f"Monthly bookings — {sel} vs average room", hovermode="x unified")
            show(style_fig(fig))

# ======================================================================
# HYPOTHESIS TESTS
# ======================================================================
with tab_hyp:
    alpha = st.select_slider("Significance level (α)", options=[0.01, 0.05, 0.10], value=0.05)
    st.caption("Tests recompute live on the filtered data. Notebook results on the full dataset remain the reference values for the report.")

    section("H1 — Are bookings equally distributed across rooms?", "Chi-square goodness-of-fit against equal demand.")
    rc_h = fdf["room_label"].value_counts()
    rc_h = rc_h[rc_h.index != MISSING]
    H1 = None
    if len(rc_h) >= 2:
        obs = rc_h.to_numpy(float)
        exp = np.full_like(obs, obs.mean())
        chi2, p = chisquare(obs, exp)
        kk = len(obs)
        w = np.sqrt(chi2 / (obs.sum() * (kk - 1)))
        H1 = dict(rooms=rc_h.index, obs=obs, exp=exp, chi2=chi2, p=p, df=kk - 1, w=w)

        m = st.columns(4)
        m[0].metric("χ²", f"{chi2:.2f}")
        m[1].metric("Degrees of freedom", kk - 1)
        m[2].metric("p-value", f"{p:.2g}")
        m[3].metric("Effect size (w)", f"{w:.2f}", strength_label(w, "w"), delta_color="off")
        rej = p < alpha
        st.markdown(f'<span class="pill {"bad" if rej else "ok"}">{"Reject H₀" if rej else "Fail to reject H₀"} (α = {alpha})</span> '
                    f'Room demand is {"statistically uneven" if rej else "consistent with equal demand"}; '
                    f'effect size is <b>{strength_label(w, "w")}</b>.', unsafe_allow_html=True)
        cmp = pd.DataFrame({"Room": rc_h.index, "Observed": obs.astype(int), "Expected": exp.round(1)})
        cmp = cmp.iloc[np.argsort([_room_sort_key(x) for x in cmp["Room"]])]
        fig = go.Figure()
        fig.add_bar(x=cmp["Room"], y=cmp["Observed"], name="Observed", marker_color=TEAL, marker_line_color="#F4F6F8", marker_line_width=2)
        fig.add_scatter(x=cmp["Room"], y=cmp["Expected"], name="Expected if equal", mode="lines+markers",
                        line=dict(dash="dash", color=AMBER, width=2.5), marker=dict(size=9))
        fig.update_layout(title="Observed vs expected bookings per room")
        show(style_fig(fig, 340))
        if (exp < 5).any():
            st.warning("Some expected counts are below 5. The chi-square approximation may be unreliable.")
    else:
        st.info("At least two rooms are needed to test H1 under these filters.")

    st.divider()
    section("H2 — Is room selection associated with purpose?", "Chi-square test of independence on the room × purpose table.")
    ct2 = pd.crosstab(fdf["room_label"], fdf["purpose_clean"])
    # B4 — prune empty rows/cols BEFORE shape check
    ct2 = ct2.loc[ct2.sum(axis=1) > 0, ct2.sum(axis=0) > 0]
    ct2 = ct2.drop(index=MISSING, errors="ignore").drop(columns=MISSING, errors="ignore")
    H2 = None
    if ct2.shape[0] >= 2 and ct2.shape[1] >= 2:
        chi2b, pb, dof, exp2 = chi2_contingency(ct2)
        n2 = ct2.to_numpy().sum()
        v = np.sqrt(chi2b / (n2 * (min(ct2.shape) - 1)))
        H2 = dict(ct=ct2, exp=exp2, chi2=chi2b, p=pb, df=dof, v=v, n=n2)

        m = st.columns(4)
        m[0].metric("χ²", f"{chi2b:.2f}")
        m[1].metric("Degrees of freedom", dof)
        m[2].metric("p-value", f"{pb:.2g}")
        m[3].metric("Cramér's V", f"{v:.2f}", strength_label(v, "v"), delta_color="off")
        rej = pb < alpha
        st.markdown(f'<span class="pill {"bad" if rej else "ok"}">{"Reject H₀" if rej else "Fail to reject H₀"} (α = {alpha})</span> ' +
                    (f'Significant association, but <b>{strength_label(v, "v")}</b> (V = {v:.2f}). Association ≠ causation.'
                     if rej else "No evidence of association between room and purpose."), unsafe_allow_html=True)

        resid = (ct2.to_numpy() - exp2) / np.sqrt(exp2)
        rdf = pd.DataFrame(resid, index=ct2.index, columns=ct2.columns)
        fig = px.imshow(rdf, text_auto=".1f", aspect="auto", color_continuous_scale="RdBu_r", color_continuous_midpoint=0,
                        labels={"x": "Purpose", "y": "Room", "color": "Std. residual"},
                        title="Standardised residuals (|value| > 2 ≈ notable over/under-use)")
        show(style_fig(fig, 440))
        small = (exp2 < 5).sum() / exp2.size * 100
        if small > 20:
            st.warning(f"{small:.0f}% of expected cells are below 5. Combine rare purposes or collect more data before relying on this p-value.")
        for (rm, pu), val in rdf.stack(future_stack=True).sort_values(key=np.abs, ascending=False).head(3).items():
            insight(f"**{rm} × {pu}**: {'more' if val > 0 else 'fewer'} bookings than expected (residual {val:+.1f}).")
    else:
        st.info("Need at least 2 rooms × 2 purposes under the current filters.")

# ======================================================================
# HOW WE ANALYSE
# ======================================================================
with tab_how:
    section("From raw bookings to findings", "Every number in this dashboard follows the same six-step pipeline. Counts below are live.")
    n_all = len(df)
    n_ts = int(df["timestamp"].notna().sum())
    n_room = int((df["room_label"] != MISSING).sum())
    n_pur = int((df["purpose_clean"] != MISSING).sum())
    n_val = int(df["duration_valid"].sum())
    n_dup = int(df.duplicated().sum())
    steps = [
        ("Collect", "Booking records exported from the library discussion-room log into one cleaned CSV.", f"{n_all:,} rows loaded"),
        ("Protect privacy", "Name, student ID, mobile number and raw text lines are dropped at load time, before anything is shown or exported.",
         f"{len(META['dropped'])} identifier column(s) removed"),
        ("Derive features", "Parse timestamps; derive year, month, weekday and hour; standardise room labels and purposes; compute duration = check-out − check-in.",
         f"{n_ts:,} usable timestamps"),
        ("Validate", "Flag durations that are negative or longer than 12 h (likely AM/PM entry errors). Flagged — never silently corrected.",
         f"{n_all - n_val:,} flagged · {n_dup:,} exact duplicates"),
        # M1 — NumPy + M2 — Matplotlib called out explicitly
        ("Analyse",
         "Descriptive statistics on the filtered view, then two chi-square tests (SciPy). "
         "NumPy builds the expected-count vector and the effect sizes (Cohen's w, Cramér's V). "
         "Matplotlib in the companion notebook reproduces every chart for verification.",
         "H1 goodness-of-fit · H2 independence"),
        ("Communicate", "Interactive charts, auto-generated insights, and de-identified CSV / summary exports.", "Filters recompute everything live"),
    ]
    html = '<div class="steps">' + "".join(
        f'<div class="step"><div class="n">{i}</div><div class="h">{h}</div><div class="d">{d}</div><div class="stat">{s}</div></div>'
        for i, (h, d, s) in enumerate(steps, 1)) + "</div>"
    st.markdown(html, unsafe_allow_html=True)

    f1, f2 = st.columns([1.1, 1])
    with f1:
        stages = ["All records", "With timestamp", "With known room", "With known purpose", "With valid duration"]
        nums = [n_all, n_ts, n_room, n_pur, n_val]
        fig = go.Figure(go.Funnel(y=stages, x=nums, textinfo="value+percent initial",
                                  marker=dict(color=[NAVY, TEAL, "#5EAAB0", AMBER, SLATE]),
                                  connector=dict(line=dict(color="#DCE3E8"))))
        fig.update_layout(title="How many records survive each quality check? (full dataset)")
        show(style_fig(fig, 360))
    with f2:
        section("Reading the funnel")
        st.markdown(
            "- Count-based findings (rooms, purposes, weekdays) rely on the **room**, **purpose** and **timestamp** stages.\n"
            "- Duration findings rely on the last stage only, so they use the smallest sample.\n"
            "- That is why the dashboard calls count-based results **more reliable** than duration-based ones.")
        if n_all:
            weakest = min(zip(nums[1:], stages[1:]))
            insight(f"Weakest field: **{weakest[1].replace('With ', '')}** — {weakest[0] / n_all * 100:.1f}% of records are usable.")

    section("Metric definitions", "Exactly how each headline number is computed.")
    table(pd.DataFrame([
        ("Total bookings", "Rows remaining after the sidebar filters", "A booking is a reservation, not verified occupancy"),
        ("Busiest room / top purpose", "Mode of the room / purpose label, excluding 'Missing / unclear'", "Ties resolve to the first label"),
        ("Median duration", "Median of (check-out − check-in) in minutes, valid records only (0–720 min)", "Median resists outliers better than the mean"),
        ("Data validity", "Share of filtered rows whose duration is within 0–720 min", "Does not imply the duration is correct, only plausible"),
        ("Unusual period (±2σ)", "Count with |z| > 2, z = (count − mean) / standard deviation across periods", "A prompt to investigate, not proof of an event"),
        ("Rolling average", "Mean of the last k periods per series", "Smooths noise; lags sharp changes"),
        # M1 — NumPy row added
        ("NumPy calculations", "np.full_like → expected counts; np.sqrt → Cohen's w / Cramér's V; np.abs → top residuals",
         "Same functions run in the notebook for reproducibility"),
    ], columns=["Metric", "How it is computed", "Caveat"]), hide_index=True)

    section("Hypothesis tests, step by step", "What each test asks, how the statistic is built, and how to read the result.")
    h1c, h2c = st.columns(2)
    with h1c:
        st.markdown("##### H1 · Equal demand across rooms")
        st.markdown("**H₀:** every room receives the same number of bookings.  \n**H₁:** at least one room is booked more or less often.")
        st.latex(r"\chi^2=\sum_i \frac{(O_i-E_i)^2}{E_i},\qquad E_i=\frac{N}{k},\qquad df=k-1")
        st.latex(r"w=\sqrt{\frac{\chi^2}{N\,(k-1)}}\quad\text{(Cohen's }w\text{)}")
        st.caption("Effect size guide: < 0.1 negligible · 0.1–0.3 small · 0.3–0.5 medium · ≥ 0.5 large")
    with h2c:
        st.markdown("##### H2 · Room choice vs purpose")
        st.markdown("**H₀:** room and purpose are independent.  \n**H₁:** some purposes prefer some rooms.")
        st.latex(r"E_{ij}=\frac{R_i\,C_j}{N},\qquad \chi^2=\sum_{i,j}\frac{(O_{ij}-E_{ij})^2}{E_{ij}},\qquad df=(r-1)(c-1)")
        st.latex(r"V=\sqrt{\frac{\chi^2}{N\,(\min(r,c)-1)}}\quad\text{(Cramér's }V\text{)}")
        st.caption("Effect size guide: < 0.1 negligible · 0.1–0.2 small · 0.2–0.3 medium · ≥ 0.3 large")

    st.markdown("**Decision rule:** if p < α, reject H₀. A tiny p-value on a large dataset can still hide a small effect, "
                "so the dashboard always reports the effect size next to the p-value.")

    section("Worked example on your current filters", "The H1 test, row by row — see exactly where the χ² comes from.")
    if H1 is not None:
        contrib = (H1["obs"] - H1["exp"]) ** 2 / H1["exp"]
        wk = pd.DataFrame({"Room": H1["rooms"], "Observed (O)": H1["obs"].astype(int), "Expected (E)": H1["exp"].round(1),
                           "O − E": (H1["obs"] - H1["exp"]).round(1), "(O−E)²/E": contrib.round(2),
                           "% of χ²": (contrib / contrib.sum() * 100).round(1) if contrib.sum() > 0 else 0})
        wk = wk.iloc[np.argsort([_room_sort_key(x) for x in wk["Room"]])]
        wa, wb = st.columns([1.1, 1])
        with wa:
            table(wk, hide_index=True, column_config={
                "% of χ²": st.column_config.ProgressColumn("% of χ²", min_value=0, max_value=100, format="%.1f%%")})
            st.markdown(f"**Σ (O−E)²/E = {contrib.sum():.2f}** with **{H1['df']}** degrees of freedom → "
                        f"p = **{H1['p']:.2g}** → {'reject' if H1['p'] < alpha else 'fail to reject'} H₀ at α = {alpha}.")
        with wb:
            fig = px.bar(wk, x="Room", y="(O−E)²/E", title="Which rooms drive the χ²?", text="(O−E)²/E")
            fig.update_traces(marker_color=AMBER, textposition="outside")
            show(style_fig(fig, 320))
    else:
        st.info("Select at least two rooms to see the worked example.")

    with st.expander("Assumptions & limitations", expanded=False):
        st.markdown(
            "- **Reservation ≠ occupancy.** No-shows, cancellations and early releases are not recorded.\n"
            "- **Submission hour ≠ use hour.** Hour-of-day charts show when bookings were made.\n"
            "- **Independence.** Chi-square assumes bookings are independent; repeat bookers and group bookings can violate this.\n"
            "- **Expected counts.** Results are flagged when expected counts fall below 5 (small-sample warning).\n"
            "- **Equal-demand benchmark.** H1 treats rooms as interchangeable; in reality capacity and location differ.\n"
            "- **Flagged durations are excluded, not repaired**, so duration statistics describe the valid subset only.\n"
            "- **Association ≠ causation.** H2 shows that patterns exist, not why.")

    with st.expander("Reproduce the tests in plain Python", expanded=False):
        st.code(
            "from scipy.stats import chisquare, chi2_contingency\n"
            "import numpy as np, pandas as pd\n\n"
            "# H1: equal demand across rooms\n"
            "obs = df['room_label'].value_counts().to_numpy(float)\n"
            "chi2, p = chisquare(obs, np.full_like(obs, obs.mean()))\n"
            "w = np.sqrt(chi2 / (obs.sum() * (len(obs) - 1)))\n\n"
            "# H2: room x purpose association\n"
            "ct = pd.crosstab(df['room_label'], df['purpose_clean'])\n"
            "chi2, p, dof, exp = chi2_contingency(ct)\n"
            "V = np.sqrt(chi2 / (ct.to_numpy().sum() * (min(ct.shape) - 1)))",
            language="python")

    # M2 + M4 — reproducibility caption
    st.caption(
        "Reproducibility: `src/parser.py` → `src/clean.py` → `src/analysis.py` → "
        "`discussion_room_bookings_cleaned.csv` → this dashboard. "
        "Companion notebook `Discussion_Room_Booking_Analysis.ipynb` reproduces every chart "
        "with Matplotlib/Seaborn so the analysis is verified in two plotting stacks."
    )

# ======================================================================
# DATA QUALITY
# ======================================================================
with tab_qual:
    section("Completeness of key fields")
    comp = pd.Series({"Timestamp": fdf["timestamp"].notna().mean(), "Room": (fdf["room_label"] != MISSING).mean(),
                      "Purpose": (fdf["purpose_clean"] != MISSING).mean(), "Valid duration": fdf["duration_valid"].mean()}) * 100
    for col, (name, pct) in zip(st.columns(len(comp)), comp.items()):
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=pct, number={"suffix": "%", "valueformat": ".1f", "font": {"color": NAVY, "size": 28}},
            title={"text": name, "font": {"size": 13, "color": "#536574"}},
            gauge={"axis": {"range": [0, 100], "tickcolor": SAND}, "bar": {"color": TEAL}, "bgcolor": "#FFFFFF", "borderwidth": 0,
                   "steps": [{"range": [0, 70], "color": "#F3E6E5"}, {"range": [70, 90], "color": "#F5EFDF"},
                             {"range": [90, 100], "color": "#E5F0E9"}]}))
        fig.update_layout(height=230, paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=50, b=10),
                          font=dict(family="Inter, Arial, sans-serif", color=NAVY))
        with col:
            show(fig)

    section("Flagged records")
    neg = int((fdf["duration_minutes_calculated"] < 0).sum())
    big = int((fdf["duration_minutes_calculated"] > 720).sum())
    dup = int(fdf.duplicated().sum())
    table(pd.DataFrame({
        "Issue": ["Negative duration", "Duration > 12 h", "Exact duplicates"],
        "Count": [neg, big, dup],
        "Share of filtered %": [round(x / len(fdf) * 100, 2) for x in (neg, big, dup)],
        "Interpretation": ["Check-out earlier than check-in — fits AM/PM entry errors", "Implausibly long for a discussion room", "Same row repeated"],
    }), hide_index=True)
    st.info("Invalid durations are **flagged, not corrected**, so count-based findings are more reliable than duration-based findings.")
    with st.expander("Recommendations for future data collection", expanded=True):
        st.markdown("- Use **dropdowns** for room and purpose\n- Use a **validated time picker** for check-in/check-out\n"
                    "- Generate an **auto booking ID**; validate check-out > check-in\n- Record **cancellations and actual room release**\n"
                    "- Store data in a **structured database**, not PDF exports\n- Keep **personal identifiers separate** from analytical tables")

# ======================================================================
# DATA & EXPORT
# ======================================================================
with tab_data:
    section("Filtered records (identifiers removed)")
    q = st.text_input("🔎 Search any text column", placeholder="e.g. study, group, Room 3")
    view_df = fdf.drop(columns=["date"], errors="ignore")
    if q:
        text_cols = view_df.select_dtypes(include=["object", "string"]).columns
        hit = np.zeros(len(view_df), dtype=bool)
        for col_ in text_cols:
            hit |= view_df[col_].astype(str).str.contains(q, case=False, na=False, regex=False).to_numpy()
        view_df = view_df[hit]
    st.caption(f"Showing up to 500 of {len(view_df):,} rows.")
    table(view_df.head(500))

    summary = (f"# Discussion Room Booking Summary\n\n- Period: {d0} to {d1}\n- Bookings: {len(fdf):,}\n"
               f"- Busiest room: {known_rooms.idxmax() if len(known_rooms) else 'n/a'}\n"
               f"- Top purpose: {known_purposes.idxmax() if len(known_purposes) else 'n/a'}\n")
    if len(valid_dur):
        summary += f"- Median valid duration: {valid_dur.median():.0f} min\n"
    summary += f"- Valid duration share: {fdf['duration_valid'].mean() * 100:.1f}%\n- Flagged durations (full dataset): {flagged_total:,}\n"
    if H1 is not None:
        summary += f"- H1 (equal room demand): chi2={H1['chi2']:.2f}, df={H1['df']}, p={H1['p']:.2g}, w={H1['w']:.2f}\n"
    if H2 is not None:
        summary += f"- H2 (room x purpose): chi2={H2['chi2']:.2f}, df={H2['df']}, p={H2['p']:.2g}, V={H2['v']:.2f}\n"
    summary += "\n_A booking is a reservation, not verified occupancy. Identifiers excluded._\n"

    st.divider()
    b1, b2 = st.columns(2)

    # B3 — clean year column in export (no 2024.0)
    export_df = (
        fdf.drop(columns=["date"], errors="ignore")
           .assign(year=lambda d: d["year"].astype("Int64").astype("string"))
    )
    b1.download_button("⬇️ Download filtered CSV", export_df.to_csv(index=False).encode("utf-8"),
                       file_name="filtered_bookings.csv", mime="text/csv", use_container_width=True)
    b2.download_button("⬇️ Download summary (Markdown)", summary.encode("utf-8"),
                       file_name="booking_summary.md", mime="text/markdown", use_container_width=True)
    st.caption("Only de-identified columns are exported.")

    # M5 — deliverables listed in footer
    st.caption("Documentation lives in `docs/`. See sidebar → 📚 Documentation.")

st.markdown(
    f'<div class="footer">Discussion Room Booking Analytics · v6.0 · '
    f'Generated {datetime.now():%d %b %Y, %H:%M} · PRG405 · '
    'Deliverables: app.py · notebooks/ · docs/ · presentation/</div>',
    unsafe_allow_html=True)