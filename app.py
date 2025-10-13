# app.py
import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus

# --------- Config / API keys ----------
# Try Streamlit secrets first then env vars
NUTR_APP_ID = st.secrets.get("nutritionix", {}).get("app_id") if st.secrets else None
NUTR_APP_KEY = st.secrets.get("nutritionix", {}).get("app_key") if st.secrets else None
if not NUTR_APP_ID:
    NUTR_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
if not NUTR_APP_KEY:
    NUTR_APP_KEY = os.getenv("NUTRITIONIX_APP_KEY")

# Nutritionix endpoints (natural language)
NUTRITIONIX_URL = "https://trackapi.nutritionix.com/v2/natural/nutrients"

# OpenFoodFacts endpoint template
OFF_PRODUCT_URL = "https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

# --------- Helpers ----------
def query_nutritionix(nl_text):
    if not (NUTR_APP_ID and NUTR_APP_KEY):
        raise ValueError("Nutritionix API keys not set. See README to set them.")
    headers = {
        "x-app-id": NUTR_APP_ID,
        "x-app-key": NUTR_APP_KEY,
        "Content-Type": "application/json",
        "x-remote-user-id": "0"
    }
    payload = {"query": nl_text}
    resp = requests.post(NUTRITIONIX_URL, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

def lookup_barcode_off(barcode):
    url = OFF_PRODUCT_URL.format(barcode=barcode)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def foods_to_dataframe(nutriix_json):
    rows = []
    for f in nutriix_json.get("foods", []):
        row = {
            "name": f.get("food_name"),
            "serving_qty": f.get("serving_qty"),
            "serving_unit": f.get("serving_unit"),
            "calories": f.get("nf_calories"),
            "total_fat_g": f.get("nf_total_fat"),
            "saturated_fat_g": f.get("nf_saturated_fat"),
            "cholesterol_mg": f.get("nf_cholesterol"),
            "sodium_mg": f.get("nf_sodium"),
            "total_carbs_g": f.get("nf_total_carbohydrate"),
            "fiber_g": f.get("nf_dietary_fiber"),
            "sugars_g": f.get("nf_sugars"),
            "protein_g": f.get("nf_protein")
        }
        rows.append(row)
    return pd.DataFrame(rows)

# --------- Streamlit UI ----------
st.set_page_config(page_title="AI Diet Tracker", page_icon="🥗", layout="centered")

st.title("AI Diet Tracker — Major Project")
st.markdown("Natural-language food input powered by Nutritionix. Barcode lookup powered by OpenFoodFacts.")

# Sidebar: daily target and simple controls
st.sidebar.header("User / Settings")
cal_target = st.sidebar.number_input("Daily calorie target (kcal)", value=2000, step=50)
if "log" not in st.session_state:
    st.session_state.log = []  # list of dicts: {timestamp, name, calories, protein, carbs, fat}

# --- Input: Natural language
st.subheader("1) Add meal by typing (e.g. '1 cup rice and 150g chicken')")
nl_input = st.text_area("Describe what you ate", value="", placeholder="e.g. 2 scrambled eggs, 1 slice toast, 1 apple")
if st.button("Analyze & Add meal (NL)"):
    if not nl_input.strip():
        st.warning("Type something first.")
    else:
        try:
            resp = query_nutritionix(nl_input)
            df = foods_to_dataframe(resp)
            # Combine totals
            totals = df[["calories", "protein_g", "total_carbs_g", "total_fat_g"]].sum()
            item_name = ", ".join(df["name"].astype(str).tolist())
            entry = {
                "timestamp": datetime.now().isoformat(),
                "name": item_name,
                "calories": float(totals["calories"] or 0),
                "protein_g": float(totals["protein_g"] or 0),
                "carbs_g": float(totals["total_carbs_g"] or 0),
                "fat_g": float(totals["total_fat_g"] or 0)
            }
            st.session_state.log.append(entry)
            st.success(f"Added: {entry['name']} — {entry['calories']:.0f} kcal")
            st.dataframe(df)
        except Exception as e:
            st.exception(e)

# --- Input: Barcode lookup
st.subheader("2) Lookup packaged food by barcode (EAN/UPC)")
barcode = st.text_input("Enter barcode (numbers only)", value="")
if st.button("Lookup barcode"):
    if not barcode.strip():
        st.warning("Enter barcode first.")
    else:
        try:
            j = lookup_barcode_off(barcode.strip())
            if j.get("status") == 1:
                prod = j["product"]
                pname = prod.get("product_name") or prod.get("generic_name") or "Unnamed product"
                nutriments = prod.get("nutriments", {})
                # Many OFF values are per 100g or per serving; we'll try per serving if available else per 100g
                calories = nutriments.get("energy_kcal_serving") or nutriments.get("energy-kcal_serving") or nutriments.get("energy-kcal_100g") or nutriments.get("energy_kcal_100g") or nutriments.get("energy_100g")
                # Normalize calories
                try:
                    calories = float(calories)
                except:
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
                st.json(prod)
            else:
                st.error("Product not found in OpenFoodFacts.")
        except Exception as e:
            st.exception(e)

# --- Display today's log and summary
st.subheader("3) Today's log")
if st.session_state.log:
    df_log = pd.DataFrame(st.session_state.log)
    # Convert timestamp to readable
    df_log["time"] = pd.to_datetime(df_log["timestamp"]).dt.strftime("%H:%M:%S")
    st.dataframe(df_log[["time", "name", "calories", "protein_g", "carbs_g", "fat_g"]])
    totals = df_log[["calories", "protein_g", "carbs_g", "fat_g"]].sum()
    st.markdown(f"**Totals:** {totals['calories']:.0f} kcal • Protein {totals['protein_g']:.1f} g • Carbs {totals['carbs_g']:.1f} g • Fat {totals['fat_g']:.1f} g")
    # Simple progress bar toward calorie target
    pct = min(1.0, totals["calories"] / (cal_target if cal_target>0 else 1))
    st.progress(pct)
    st.write(f"{totals['calories']:.0f} / {cal_target} kcal ({pct*100:.0f}%)")
    # Chart
    st.bar_chart(df_log.set_index("time")["calories"])
    # Export CSV
    csv = df_log.to_csv(index=False)
    st.download_button("Download CSV of log", csv, file_name="diet_log.csv", mime="text/csv")
else:
    st.info("No meals logged yet. Add a meal above.")

# --- Clear or reset
st.sidebar.markdown("---")
if st.sidebar.button("Clear today's log"):
    st.session_state.log = []
    st.sidebar.success("Log cleared.")
