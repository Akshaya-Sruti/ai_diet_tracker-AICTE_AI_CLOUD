# app.py — AI Diet Tracker powered by USDA FoodData Central
import os
import html
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# --------- Config / API keys ----------
# USDA FoodData Central key: .streamlit/secrets.toml [usda] api_key,
# or env USDA_API_KEY / FDC_API_KEY. Never hardcode or print it.
def _get_usda_key():
    key = None
    try:
        if st.secrets and "usda" in st.secrets:
            key = st.secrets["usda"].get("api_key")
    except Exception:
        key = None
    if not key:
        key = os.getenv("USDA_API_KEY") or os.getenv("FDC_API_KEY")
    return (key or "").strip() or None


USDA_API_KEY = _get_usda_key()

# USDA FoodData Central endpoints
USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
USDA_FOOD_URL = "https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"

# OpenFoodFacts endpoint template (barcode fallback)
OFF_PRODUCT_URL = "https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

# Nutrient numbers used by FDC: Energy=kcal 208, Protein 203, Fat 204, Carbs 205
TARGET_NUTRIENTS = "208,203,204,205"


# --------- Helpers: USDA FoodData Central ----------
def _require_key():
    if not USDA_API_KEY:
        raise ValueError(
            "USDA API key not set. Add it to .streamlit/secrets.toml as "
            '[usda] api_key = "YOUR_KEY" or set env USDA_API_KEY.'
        )


def usda_search(query, page_size=10, data_types=None):
    """Search FDC for foods matching query. Returns list of food dicts."""
    _require_key()
    params = {"api_key": USDA_API_KEY, "query": query, "pageSize": page_size}
    if data_types:
        params["dataType"] = ",".join(data_types)
    resp = requests.get(USDA_SEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        return data.get("foods", []) or []
    if isinstance(data, list):
        return data
    return []


def usda_food_details(fdc_id):
    """Fetch full details (nutrients) for one FDC id."""
    _require_key()
    url = USDA_FOOD_URL.format(fdc_id=fdc_id)
    params = {"api_key": USDA_API_KEY, "nutrients": TARGET_NUTRIENTS}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _nutrient_from_list(food_nutrients, numbers, names):
    """Pull amount from a foodNutrients list (handles full + abridged shapes)."""
    numbers = {str(n) for n in numbers}
    names = {n.lower() for n in names}
    for n in food_nutrients or []:
        nut = n.get("nutrient", {}) or {}
        num = str(n.get("number", nut.get("number", "")))
        name = str(n.get("name", nut.get("name", ""))).lower()
        unit = str(n.get("unitName", nut.get("unitName", ""))).lower()
        if num in numbers or name in names:
            # Energy: only accept kcal (FDC also returns kJ under a nearby id)
            if numbers == {"208"} and unit and unit not in ("kcal", "cal"):
                continue
            try:
                return float(n.get("amount", n.get("value", 0)) or 0)
            except (TypeError, ValueError):
                return 0.0
    return None


def extract_usda_nutrients(detail):
    """Return per-100g (or per-serving scaled) nutrients + serving metadata.

    Prefers labelNutrients (Branded, per serving) then falls back to
    foodNutrients (per 100 g). Returns dict with basis info.
    """
    label = detail.get("labelNutrients", {}) or {}
    serving_g = detail.get("servingSize")  # branded serving size in g
    try:
        serving_g = float(serving_g) if serving_g else None
    except (TypeError, ValueError):
        serving_g = None

    def _lv(*names):
        for nm in names:
            d = label.get(nm)
            if isinstance(d, dict) and d.get("value") is not None:
                try:
                    return float(d["value"])
                except (TypeError, ValueError):
                    pass
        return None

    if label:
        cals = _lv("calories")
        prot = _lv("protein")
        fat = _lv("fat")
        carbs = _lv("carbohydrates")
        if any(v is not None for v in (cals, prot, fat, carbs)):
            return {
                "basis": "serving" if serving_g else "label",
                "serving_g": serving_g,
                "calories": cals or 0.0,
                "protein_g": prot or 0.0,
                "carbs_g": carbs or 0.0,
                "fat_g": fat or 0.0,
            }

    fns = detail.get("foodNutrients", []) or []
    cals = _nutrient_from_list(fns, ("208",), ("energy",)) or 0.0
    prot = _nutrient_from_list(fns, ("203",), ("protein",)) or 0.0
    fat = _nutrient_from_list(fns, ("204",), ("total lipid (fat)", "total lipid")) or 0.0
    carbs = _nutrient_from_list(fns, ("205",), ("carbohydrate, by difference", "carbohydrate")) or 0.0
    return {
        "basis": "100g",
        "serving_g": serving_g,
        "calories": cals,
        "protein_g": prot,
        "carbs_g": carbs,
        "fat_g": fat,
    }


def scale_nutrients(nut, grams):
    """Scale extracted nutrients to the eaten weight in grams."""
    grams = float(grams or 0)
    if nut.get("basis") == "serving" and nut.get("serving_g"):
        factor = grams / nut["serving_g"] if nut["serving_g"] else 1.0
    else:  # per-100g basis (or label without serving size)
        factor = grams / 100.0
    return {
        "calories": nut["calories"] * factor,
        "protein_g": nut["protein_g"] * factor,
        "carbs_g": nut["carbs_g"] * factor,
        "fat_g": nut["fat_g"] * factor,
    }


def lookup_barcode_off(barcode):
    """OpenFoodFacts fallback for barcode lookup."""
    url = OFF_PRODUCT_URL.format(barcode=barcode)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def lookup_barcode_usda(barcode):
    """Find a Branded food in FDC by GTIN/UPC. Returns (food_summary, detail)."""
    code = barcode.strip().lstrip("0") or "0"
    results = usda_search(barcode.strip(), page_size=25, data_types=["Branded"])
    for f in results:
        gtin = str(f.get("gtinUpc") or "").strip().lstrip("0") or "0"
        if gtin and (gtin == code or gtin == barcode.strip()):
            return f, usda_food_details(f["fdcId"])
    # No exact GTIN match: fall back to top branded hit if the query was the barcode
    if results:
        top = results[0]
        return top, usda_food_details(top["fdcId"])
    return None, None


# --------- Page config ----------
st.set_page_config(page_title="AI Diet Tracker", page_icon="🥗", layout="wide")

# --------- Session state ----------
if "log" not in st.session_state:
    st.session_state.log = []  # list of dicts: {timestamp, name, calories, protein_g, carbs_g, fat_g}
if "usda_results" not in st.session_state:
    st.session_state.usda_results = []

# --------- Styles (light theme enforced; all text dark for visibility) ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #F3F5EC;
  --ink: #17231C;
  --green: #4E9B5F;
  --green-deep: #2F6B3C;
  --lime: #B8D96B;
  --peach: #E8A54B;
  --card: #FFFFFF;
  --muted: #5F665F;
  --border: #DFE5D5;
  --danger: #D96C6C;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg);
  color-scheme: light;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--ink);
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

/* Force readable dark text on the light background (fixes white-on-white) */
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] div[data-testid="stMarkdownContainer"] p,
[data-testid="stAppViewContainer"] div[data-testid="stMarkdownContainer"] span,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] div[data-testid="stWidgetLabel"] label,
[data-testid="stAppViewContainer"] div[data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label {
  color: var(--ink) !important;
}
[data-testid="stAppViewContainer"] .stCaption, [data-testid="stSidebar"] .stCaption {
  color: var(--muted) !important;
}

.block-container { max-width: 1120px; padding-top: 2rem; padding-bottom: 3rem; }

/* Sidebar (tight top spacing — no empty gap above brand) */
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] .block-container { padding-top: 0.5rem !important; }
div[data-testid="stSidebarUserContent"] { padding-top: 0 !important; }
[data-testid="stSidebarHeader"] { padding-top: 0.25rem !important; }
.brand-mark { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.brand-dot {
  width: 32px; height: 32px; border-radius: 10px;
  background: var(--ink); color: #fff !important;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 16px;
}
.brand-name { font-weight: 800; letter-spacing: 0.08em; font-size: 13px; color: var(--ink) !important; }
.brand-sub { font-size: 12px; color: var(--muted) !important; margin: 2px 0 16px 0; }
.side-label { font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: var(--muted) !important; margin: 18px 0 6px 0; }

/* Type */
.eyebrow {
  display: inline-block; font-size: 11.5px; font-weight: 800; letter-spacing: 0.14em;
  color: #fff !important; background: var(--green-deep);
  border-radius: 999px; padding: 6px 14px; margin-bottom: 10px;
}
.hero-title { font-size: 42px; line-height: 1.05; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 6px 0; color: var(--ink) !important; }
.hero-title em { font-style: normal; color: var(--green-deep) !important; }
.hero-sub { font-size: 15px; color: var(--muted) !important; margin: 0 0 4px 0; }
.hero-sub b, .section-p b { color: var(--ink) !important; }
.date-pill {
  display: inline-block; font-size: 12px; font-weight: 600; color: var(--muted) !important;
  background: #fff; border: 1px solid var(--border); border-radius: 999px; padding: 5px 12px; margin-top: 10px;
}

/* Cards */
.dt-card {
  background: var(--card); border: 1px solid var(--border); border-radius: 18px;
  padding: 22px 22px; box-shadow: 0 2px 10px rgba(47,107,60,0.07); color: var(--ink);
}
.dt-card.tight { padding: 18px; }
/* Rich dark hero card — always dark bg with cream text, no theme clash possible */
.cal-hero {
  background: #17231C; border: 1px solid #17231C; border-radius: 20px;
  padding: 26px 26px; box-shadow: 0 6px 22px rgba(23,35,28,0.25); color: #F5F7EF;
}
.cal-hero .card-eyebrow { color: var(--lime) !important; }
.cal-hero .cal-big { color: #FFFFFF !important; }
.cal-hero .cal-big small { color: #C9D4C3 !important; }
.cal-hero .cal-remain { color: #FFFFFF !important; }
.cal-hero .cal-remain span { color: #C9D4C3 !important; }
.cal-hero .track { background: rgba(255,255,255,0.16); }
/* Tinted macro cards */
.macro-tint-green { background: #E3F0E1 !important; border-color: #C6DFC2 !important; }
.macro-tint-lime { background: #EFF5D3 !important; border-color: #D7E3A6 !important; }
.macro-tint-peach { background: #FBEEDC !important; border-color: #F0D3A8 !important; }
.macro-tint-berry { background: #F3E4E4 !important; border-color: #E3BFC0 !important; }
.card-eyebrow { font-size: 11px; font-weight: 700; letter-spacing: 0.12em; color: var(--muted) !important; margin-bottom: 8px; }
.cal-big { font-size: 38px; font-weight: 800; letter-spacing: -0.02em; color: var(--ink) !important; }
.cal-big small { font-size: 16px; font-weight: 600; color: var(--muted) !important; }
.cal-remain { font-size: 13px; font-weight: 600; color: var(--ink) !important; margin-top: 8px; }
.cal-remain span { color: var(--muted) !important; font-weight: 500; }

.track { height: 10px; background: #ECEFE7; border-radius: 999px; margin-top: 14px; overflow: hidden; }
.fill { height: 100%; background: linear-gradient(90deg, var(--green), var(--lime)); border-radius: 999px; transition: width .4s ease; }

.macro-dot { width: 10px; height: 10px; border-radius: 999px; display: inline-block; margin-right: 8px; vertical-align: middle; }
.macro-val { font-size: 26px; font-weight: 800; letter-spacing: -0.01em; margin: 6px 0 2px 0; color: var(--ink) !important; }
.macro-val small { font-size: 13px; font-weight: 600; color: var(--muted) !important; }
.macro-label { font-size: 12px; font-weight: 700; letter-spacing: 0.08em; color: var(--muted) !important; }

.section-h { font-size: 20px; font-weight: 800; letter-spacing: -0.01em; margin: 0; color: var(--ink) !important; }
.section-p { font-size: 13.5px; color: var(--muted) !important; margin: 4px 0 0 0; }

.meal-row {
  display: flex; justify-content: space-between; align-items: center; gap: 14px;
  background: #fff; border: 1px solid var(--border); border-radius: 14px; padding: 14px 16px; margin-bottom: 10px;
}
.meal-name { font-weight: 700; font-size: 14.5px; color: var(--ink) !important; }
.meal-time { font-size: 12px; color: var(--muted) !important; margin-top: 2px; }
.meal-kcal { font-weight: 800; font-size: 15px; white-space: nowrap; color: var(--ink) !important; }
.meal-macros { font-size: 12px; color: var(--muted) !important; margin-top: 2px; white-space: nowrap; }

.empty-wrap { text-align: center; padding: 28px 12px 22px 12px; }
.empty-icon {
  width: 52px; height: 52px; border-radius: 16px; background: #EFF4E8; color: var(--green) !important;
  display: flex; align-items: center; justify-content: center; font-size: 24px; margin: 0 auto 12px auto;
}
.empty-title { font-weight: 800; font-size: 16px; color: var(--ink) !important; }
.empty-sub { font-size: 13.5px; color: var(--muted) !important; margin-top: 4px; }
.key-hint { font-size: 12.5px; color: var(--muted) !important; background: #FFF8E8; border: 1px solid #EFE3B8; border-radius: 12px; padding: 10px 12px; }

/* Inputs + buttons (dark text inside white fields) */
div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
  border-radius: 14px !important; border: 1px solid var(--border) !important;
  background: #fff !important; color: var(--ink) !important; padding: 12px 14px !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
  border-radius: 14px !important; border: 1px solid var(--border) !important;
  background: #fff !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] span { color: var(--ink) !important; }
div[data-testid="stTextArea"] textarea::placeholder, div[data-testid="stTextInput"] input::placeholder {
  color: #9AA19A !important; opacity: 1;
}
div[data-testid="stTextArea"] textarea:focus, div[data-testid="stTextInput"] input:focus {
  border-color: var(--green) !important; box-shadow: 0 0 0 3px rgba(78,155,95,0.20) !important;
}
/* Selectbox dropdown renders in a portal outside the app container —
   force light menu so options are never black-on-black or white-on-white */
div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"] {
  background: #FFFFFF !important; border-radius: 12px !important;
}
ul[data-baseweb="menu"] li, div[data-baseweb="menu"] li,
ul[data-baseweb="menu"] li span, div[data-baseweb="menu"] span {
  color: #17231C !important; background: #FFFFFF !important;
}
ul[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li[aria-selected="true"] {
  background: #E7F1E4 !important;
}
ul[data-baseweb="menu"] li:hover span, ul[data-baseweb="menu"] li[aria-selected="true"] span {
  color: #17231C !important; background: transparent !important;
}
div[data-testid="stButton"] > button, div.stButton > button {
  background: var(--ink); color: #fff !important; border: none; border-radius: 12px;
  font-weight: 700; padding: 10px 18px; width: 100%;
}
div[data-testid="stButton"] > button:hover, div.stButton > button:hover { background: #24352b; color: #fff !important; border: none; }
/* Button labels render as markdown INSIDE the button — they must stay white
   on the dark button (overrides the global dark-text rule above). */
[data-testid="stAppViewContainer"] div[data-testid="stButton"] div[data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] div[data-testid="stButton"] div[data-testid="stMarkdownContainer"] p,
div[data-testid="stButton"] button p, div[data-testid="stButton"] button span {
  color: #FFFFFF !important;
}
div.stButton > button:disabled { background: #C9CFC9 !important; color: #fff !important; }
div[data-testid="stDownloadButton"] > button {
  background: #fff; color: var(--ink) !important; border: 1px solid var(--border); border-radius: 12px; font-weight: 700; width: 100%;
}
div[data-testid="stDownloadButton"] > button:hover { border-color: var(--ink); }
.danger-note { font-size: 12px; color: var(--muted) !important; }

/* Dataframes / charts / alerts */
div[data-testid="stDataFrame"] { background: #FFFFFF !important; border-radius: 14px; }
details[data-testid="stExpander"] {
  background: #FFFFFF !important; border: 1px solid var(--border) !important; border-radius: 14px;
}
details[data-testid="stExpander"] summary p,
details[data-testid="stExpander"] summary span { color: var(--ink) !important; }
details[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] p { color: var(--ink) !important; }

/* Alerts: always light card + dark text (never dark-bg mystery boxes) */
div[data-testid="stAlert"] {
  background: #FFFFFF !important; border: 1px solid var(--border) !important;
  border-radius: 14px !important; color: var(--ink) !important;
}
div[data-testid="stAlert"] p, div[data-testid="stAlert"] span,
div[data-testid="stAlert"] div, div[data-testid="stAlert"] li { color: var(--ink) !important; }
div[data-testid="stAlert"] a { color: var(--green-deep) !important; }
div[data-testid="stProgressBar"] > div > div { background-color: var(--green); }
div[data-testid="stProgressBar"] p { color: var(--ink) !important; }

/* ---- Theme lockdown: repaint every Streamlit surface light so text is
   always dark-on-light, even if the viewer toggled Dark in Streamlit's menu ---- */
[data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stSidebar"] { background: #FFFFFF !important; }
[data-testid="stSidebarNav"] { background: #FFFFFF !important; }
[data-testid="stHeader"], [data-testid="stToolbar"] { background: transparent !important; }
[data-testid="stToolbar"] button, [data-testid="stHeader"] button,
[data-testid="stToolbar"] a, [data-testid="stHeader"] a { color: var(--ink) !important; }
[data-testid="stToolbar"] svg, [data-testid="stHeader"] svg { fill: var(--ink) !important; }
[data-testid="stDecoration"] { background: var(--green) !important; }
/* number-input steppers */
div[data-testid="stNumberInput"] button {
  background: #FFFFFF !important; color: var(--ink) !important; border-color: var(--border) !important;
}
div[data-testid="stNumberInput"] button svg { fill: var(--ink) !important; }
/* selectbox arrow */
div[data-testid="stSelectbox"] svg { fill: var(--ink) !important; color: var(--ink) !important; }
/* checkboxes / radios (future-proof) */
div[data-testid="stCheckbox"] label p, div[data-testid="stRadio"] label p { color: var(--ink) !important; }
/* dataframe grid text */
div[data-testid="stDataFrame"] *, div[data-testid="stTable"] * { color: var(--ink) !important; }
/* chart container */
div[data-testid="stVegaLiteChart"] { background: transparent !important; }
/* tooltips stay dark-bg with light text */
div[data-baseweb="tooltip"] { background: #17231C !important; }
div[data-baseweb="tooltip"] * { color: #FFFFFF !important; background: transparent !important; }
/* disabled buttons: dark text on grey, never white-on-white */
div.stButton > button:disabled { background: #DDE2D8 !important; color: #5F665F !important; }
/* Real bordered containers render as product cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
  border: 1px solid var(--border) !important; border-radius: 18px !important;
  background: #FFFFFF !important; box-shadow: 0 2px 10px rgba(47,107,60,0.07);
}
/* captions + help text */
div[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }
div[data-testid="stWidgetLabel"] p { color: var(--ink) !important; }
</style>
""", unsafe_allow_html=True)

# --------- Sidebar ----------
with st.sidebar:
    st.markdown("""
    <div class="brand-mark"><div class="brand-dot">D</div><div class="brand-name">AI DIET TRACKER</div></div>
    <div class="brand-sub">A calm place to understand what you eat.</div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="side-label">NAVIGATION</div>', unsafe_allow_html=True)
    st.markdown("**Dashboard**  \n<span style='font-size:12px;color:#737A73'>Today's nutrition at a glance</span>", unsafe_allow_html=True)
    st.markdown('<div class="side-label">DAILY TARGET</div>', unsafe_allow_html=True)
    cal_target = st.number_input("Daily calorie target (kcal)", value=2000, step=50)
    st.caption("Controls the progress bar and remaining calories.")
    st.markdown('<div class="side-label">QUICK ACTIONS</div>', unsafe_allow_html=True)
    if st.button("Clear today's log"):
        st.session_state.log = []
        st.session_state.usda_results = []
        st.rerun()
    st.markdown("<div class='danger-note'>Clears all meals for today. This can't be undone.</div>", unsafe_allow_html=True)

# --------- Derived totals (computed AFTER sidebar actions so Clear refreshes instantly) ----------
if st.session_state.log:
    _df_tmp = pd.DataFrame(st.session_state.log)
    _totals = _df_tmp[["calories", "protein_g", "carbs_g", "fat_g"]].sum()
    total_cals = float(_totals["calories"] or 0)
    total_protein = float(_totals["protein_g"] or 0)
    total_carbs = float(_totals["carbs_g"] or 0)
    total_fat = float(_totals["fat_g"] or 0)
else:
    total_cals, total_protein, total_carbs, total_fat = 0.0, 0.0, 0.0, 0.0

# Recompute progress (same formula as before)
pct = min(1.0, total_cals / (cal_target if cal_target > 0 else 1))
remaining = max(0, (cal_target if cal_target else 0) - total_cals)

# --------- Hero ----------
today_str = datetime.now().strftime("%A, %B %d")
st.markdown('<div class="eyebrow">AI DIET TRACKER · USDA FOODDATA CENTRAL</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Understand <em>what you eat.</em></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Search the USDA database or scan a barcode. Stay close to your daily target.</div>', unsafe_allow_html=True)
st.markdown(f"<div><span class='date-pill'>{today_str} &nbsp;·&nbsp; {len(st.session_state.log)} meal(s) logged</span></div>", unsafe_allow_html=True)
st.write("")

if not USDA_API_KEY:
    st.markdown(
        "<div class='key-hint'><b>USDA API key missing.</b> Add it to "
        "<b>.streamlit/secrets.toml</b> as <b>[usda] api_key = \"YOUR_KEY\"</b> "
        "or set the <b>USDA_API_KEY</b> env var, then restart. "
        "Get a free key at fdc.nal.usda.gov → Get an API Key.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

# --------- Calorie overview card ----------
st.markdown(f"""
<div class="cal-hero">
  <div class="card-eyebrow">TODAY'S CALORIES</div>
  <div class="cal-big">{total_cals:,.0f} <small>/ {cal_target:,.0f} kcal</small></div>
  <div class="track"><div class="fill" style="width:{pct*100:.1f}%"></div></div>
  <div class="cal-remain">{remaining:,.0f} kcal remaining <span>· {pct*100:.0f}% of target</span></div>
</div>
""", unsafe_allow_html=True)
st.write("")

# --------- Macro cards ----------
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""<div class="dt-card tight macro-tint-green"><div><span class="macro-dot" style="background:#2F6B3C"></span><span class="macro-label">CALORIES</span></div><div class="macro-val">{total_cals:,.0f} <small>kcal</small></div><div class="section-p">Eaten today</div></div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class="dt-card tight macro-tint-lime"><div><span class="macro-dot" style="background:#7A9A1F"></span><span class="macro-label">PROTEIN</span></div><div class="macro-val">{total_protein:,.1f} <small>g</small></div><div class="section-p">Supports recovery</div></div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="dt-card tight macro-tint-peach"><div><span class="macro-dot" style="background:#E8A54B"></span><span class="macro-label">CARBS</span></div><div class="macro-val">{total_carbs:,.1f} <small>g</small></div><div class="section-p">Daily energy</div></div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""<div class="dt-card tight macro-tint-berry"><div><span class="macro-dot" style="background:#D96C6C"></span><span class="macro-label">FAT</span></div><div class="macro-val">{total_fat:,.1f} <small>g</small></div><div class="section-p">Essential intake</div></div>""", unsafe_allow_html=True)

st.write("")


def _result_label(f):
    desc = (f.get("description") or "Unnamed food").title()
    brand = f.get("brandOwner")
    dtype = f.get("dataType", "")
    extra = f" — {brand}" if brand else (f" ({dtype})" if dtype else "")
    return f"{desc}{extra}"


# --------- Input section ----------
left, right = st.columns([1.6, 1], gap="medium")
with left:
    with st.container(border=True):
        st.markdown('<div class="section-h">Add what you ate</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-p">Search the USDA FoodData Central database, pick a match, set the weight.</div>', unsafe_allow_html=True)
        st.write("")
        nl_input = st.text_input(
            "Search food",
            value="",
            placeholder="Try: cheddar cheese, banana, chicken breast",
            key="usda_query",
        )
        if st.button("Search foods (USDA)", disabled=not USDA_API_KEY):
            if not nl_input.strip():
                st.warning("Type something first.")
            else:
                try:
                    st.session_state.usda_results = usda_search(nl_input.strip(), page_size=10)
                    if not st.session_state.usda_results:
                        st.info("No matches in USDA. Try a simpler term (e.g. 'banana').")
                except Exception as e:
                    st.exception(e)

        if st.session_state.usda_results:
            options = list(range(len(st.session_state.usda_results)))
            choice = st.selectbox(
                "Pick the closest match",
                options,
                format_func=lambda i: _result_label(st.session_state.usda_results[i]),
                key="usda_choice",
            )
            grams = st.number_input("Portion (grams)", value=100.0, min_value=1.0, step=10.0, key="usda_grams")
            if st.button("Add selected food"):
                try:
                    picked = st.session_state.usda_results[choice]
                    detail = usda_food_details(picked["fdcId"])
                    nut = extract_usda_nutrients(detail)
                    scaled = scale_nutrients(nut, grams)
                    entry = {
                        "timestamp": datetime.now().isoformat(),
                        "name": f"{picked.get('description', 'Food').title()} ({float(grams):.0f} g)",
                        "calories": float(scaled["calories"] or 0),
                        "protein_g": float(scaled["protein_g"] or 0),
                        "carbs_g": float(scaled["carbs_g"] or 0),
                        "fat_g": float(scaled["fat_g"] or 0),
                    }
                    st.session_state.log.append(entry)
                    st.success(f"Added: {entry['name']} — {entry['calories']:.0f} kcal (USDA)")
                    st.rerun()
                except Exception as e:
                    st.exception(e)

with right:
    with st.container(border=True):
        st.markdown('<div class="card-eyebrow">SCAN A PRODUCT</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-h" style="font-size:18px">Packaged food?</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-p">USDA Branded foods first, OpenFoodFacts as fallback.</div>', unsafe_allow_html=True)
        st.write("")
        barcode = st.text_input("Enter barcode (numbers only)", value="")
        if st.button("Lookup barcode"):
            if not barcode.strip():
                st.warning("Enter barcode first.")
            else:
                try:
                    added = False
                    if USDA_API_KEY:
                        try:
                            summary, detail = lookup_barcode_usda(barcode.strip())
                        except Exception as e:
                            st.warning(f"USDA barcode search failed ({e}); trying OpenFoodFacts…")
                            summary, detail = None, None
                        if summary and detail:
                            nut = extract_usda_nutrients(detail)
                            serving_g = nut.get("serving_g") or 100.0
                            scaled = scale_nutrients(nut, serving_g)
                            pname = (summary.get("description") or detail.get("description") or "Unnamed product").title()
                            entry = {
                                "timestamp": datetime.now().isoformat(),
                                "name": f"{pname} ({float(serving_g):.0f} g)",
                                "calories": float(scaled["calories"] or 0),
                                "protein_g": float(scaled["protein_g"] or 0),
                                "carbs_g": float(scaled["carbs_g"] or 0),
                                "fat_g": float(scaled["fat_g"] or 0),
                            }
                            st.session_state.log.append(entry)
                            st.success(f"Added: {pname} — {entry['calories']:.0f} kcal (USDA Branded)")
                            added = True
                            st.rerun()
                    if not added:
                        j = lookup_barcode_off(barcode.strip())
                        if j.get("status") == 1:
                            prod = j["product"]
                            pname = prod.get("product_name") or prod.get("generic_name") or "Unnamed product"
                            nutriments = prod.get("nutriments", {})
                            calories = nutriments.get("energy_kcal_serving") or nutriments.get("energy-kcal_serving") or nutriments.get("energy-kcal_100g") or nutriments.get("energy_kcal_100g") or nutriments.get("energy_100g")
                            try:
                                calories = float(calories)
                            except Exception:
                                calories = None
                            entry = {
                                "timestamp": datetime.now().isoformat(),
                                "name": pname,
                                "calories": float(calories) if calories else 0.0,
                                "protein_g": float(nutriments.get("proteins_100g") or 0),
                                "carbs_g": float(nutriments.get("carbohydrates_100g") or 0),
                                "fat_g": float(nutriments.get("fat_100g") or 0)
                            }
                            st.session_state.log.append(entry)
                            st.success(f"Added: {pname} — {entry['calories']:.0f} kcal (from OpenFoodFacts)")
                            with st.expander("Product details"):
                                st.json(prod)
                            st.rerun()
                        else:
                            st.error("Product not found in USDA or OpenFoodFacts.")
                except Exception as e:
                    st.exception(e)

st.write("")

# --------- Today's meals ----------
st.markdown('<div class="section-h">Today\'s meals</div>', unsafe_allow_html=True)
st.markdown('<div class="section-p">Every entry updates your totals, chart, and export instantly.</div>', unsafe_allow_html=True)
st.write("")

if st.session_state.log:
    df_log = pd.DataFrame(st.session_state.log)
    df_log["time"] = pd.to_datetime(df_log["timestamp"]).dt.strftime("%H:%M:%S")

    cards_html = ""
    for _, r in df_log.iloc[::-1].iterrows():
        cards_html += f"""
        <div class="meal-row">
          <div><div class="meal-name">{html.escape(str(r['name']))}</div><div class="meal-time">{html.escape(str(r['time']))}</div></div>
          <div style="text-align:right"><div class="meal-kcal">{float(r['calories']):.0f} kcal</div>
          <div class="meal-macros">P {float(r['protein_g']):.1f}g · C {float(r['carbs_g']):.1f}g · F {float(r['fat_g']):.1f}g</div></div>
        </div>"""
    st.markdown(cards_html, unsafe_allow_html=True)

    with st.expander("View detailed table"):
        st.dataframe(df_log[["time", "name", "calories", "protein_g", "carbs_g", "fat_g"]], use_container_width=True)

    c1, c2 = st.columns([1.4, 1], gap="medium")
    with c1:
        with st.container(border=True):
            st.markdown('<div class="card-eyebrow">CALORIES BY MEAL</div>', unsafe_allow_html=True)
            st.bar_chart(df_log.set_index("time")["calories"])
    with c2:
        with st.container(border=True):
            st.markdown('<div class="card-eyebrow">SUMMARY</div>', unsafe_allow_html=True)
            st.markdown(f"<div class='section-p'><b>{total_cals:.0f} kcal</b> · Protein {total_protein:.1f} g · Carbs {total_carbs:.1f} g · Fat {total_fat:.1f} g</div>", unsafe_allow_html=True)
            st.write("")
            csv = df_log.to_csv(index=False)
            st.download_button("Download CSV of log", csv, file_name="diet_log.csv", mime="text/csv")
            st.markdown("<div class='danger-note'>Exports exactly what's in your log.</div>", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="dt-card"><div class="empty-wrap">
      <div class="empty-icon">🥗</div>
      <div class="empty-title">Your food log is empty.</div>
      <div class="empty-sub">Add your first meal to start tracking today's nutrition.</div>
    </div></div>
    """, unsafe_allow_html=True)
