<div align="center">

# 🥗 AI Diet Tracker

### *Eat. Track. Understand.*

**A wellness-grade nutrition dashboard powered by the USDA FoodData Central database.**

Track calories & macros in seconds — search any food, scan any barcode, watch your day take shape.

<br>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.50-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![USDA](https://img.shields.io/badge/USDA-FoodData_Central-2F6B3C?style=for-the-badge&logo=leaf&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data-150458?style=for-the-badge&logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-B8D96B?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Live_Project-4E9B5F?style=for-the-badge)

[Features](#-what-it-does) · [Quickstart](#-get-running-in-5-minutes) · [How it works](#-how-it-works) · [API](#-data--api) · [Roadmap](#-roadmap)

</div>

---

## ✨ What it does

<table>
<tr>
<td width="50%">

### 🔍 Smart food search
Type **"cheddar cheese"**, pick the closest USDA match, set the grams — done. Real government nutrient data, no guessing.

### 📷 Barcode lookup
Enter any **EAN/UPC**. The app checks **USDA Branded foods** by GTIN first, then falls back to **OpenFoodFacts**.

</td>
<td width="50%">

### 📊 Live dashboard
Dark hero calorie card, tinted macro cards, per-meal breakdown, calorie-by-meal chart — everything updates the instant you log.

### 🎯 Goals + export
Set your daily target, watch the progress bar move, then download the whole log as **CSV** for Excel / Sheets / Pandas.

</td>
</tr>
</table>

---

## 🖥️ The experience

```text
┌─────────────────────────────────────────────────┐
│  ● AI DIET TRACKER · USDA FOODDATA CENTRAL      │
│                                                 │
│  Understand what you eat.                       │
│  ─────────────────────────────                  │
│  ┌───────────────────────────────────────────┐  │
│  │  TODAY'S CALORIES                         │  │
│  │  1,284 / 2,000 kcal                       │  │
│  │  ████████████████░░░░░░  716 remaining    │  │
│  └───────────────────────────────────────────┘  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │
│  │ 1284 │ │ 82.4 │ │149.2 │ │ 41.0│             │
│  │ kcal │ │ prot │ │ carbs│ │ fat │             │
│  └──────┘ └──────┘ └──────┘ └──────┘             │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Get running in 5 minutes

### 1️⃣ Clone it

```bash
git clone https://github.com/Akshaya-Sruti/ai_diet_tracker-AICTE_AI_CLOUD.git
cd ai_diet_tracker-AICTE_AI_CLOUD
```

### 2️⃣ Get a **free** USDA API key 🔑

1. Go to 👉 **https://fdc.nal.usda.gov/api-key-signup.html**
2. Sign up with your email — key arrives in seconds
3. No credit card. ~1,000 requests/hour free quota

### 3️⃣ Set up Python

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 4️⃣ Add your key

Create `.streamlit/secrets.toml`:

```toml
[usda]
api_key = "PASTE_YOUR_KEY_HERE"
```

> 💡 Or set an env var instead: `USDA_API_KEY` (Windows: `setx USDA_API_KEY "…"`)

> 🔒 **Never commit this file.** It's already in `.gitignore`.

### 5️⃣ Run it

```bash
python -m streamlit run app.py
```

Open → **http://localhost:8501** 🎉

---

## 🧠 How it works

```text
                    ┌──────────────┐
                    │     USER     │
                    └──────┬───────┘
              ┌────────────┴────────────┐
              ▼                         ▼
     "cheddar cheese"              8901234567890
     + 100 grams                   (barcode)
              │                         │
              ▼                         ▼
   ┌─────────────────────┐   ┌───────────────────────┐
   │  USDA foods/search  │   │ USDA Branded (GTIN)   │
   │  → pick a match     │   │  → fallback:          │
   │  → food/{fdcId}     │   │ OpenFoodFacts         │
   └─────────┬───────────┘   └───────────┬───────────┘
             └─────────────┬─────────────┘
                           ▼
                  ┌────────────────┐
                  │ calories · P/C/F│  scaled to YOUR portion
                  └────────┬───────┘
                           ▼
              ┌────────────────────────┐
              │  Streamlit dashboard   │
              │  log · totals · chart  │
              │  progress · CSV export │
              └────────────────────────┘
```

### Nutrient mapping (USDA → app)

| USDA source | What it is | Basis |
|---|---|---|
| `labelNutrients` (calories, protein, fat, carbohydrates) | Branded label values | per serving (`servingSize` g) |
| `foodNutrients` #208 Energy | Calories (kcal only — kJ ignored) | per 100 g |
| `foodNutrients` #203 Protein | Protein | per 100 g |
| `foodNutrients` #204 Total lipid | Fat | per 100 g |
| `foodNutrients` #205 Carbohydrate | Carbs | per 100 g |

Everything is scaled to the grams **you** ate before it hits the log.

---

## 🗂️ Project structure

```text
ai_diet_tracker/
├── 🐍 app.py                  # the whole app: API layer + dashboard
├── 📦 requirements.txt        # streamlit · pandas · requests
├── 📖 README.md               # you are here
└── .streamlit/
    ├── 🔑 secrets.toml        # YOUR USDA key (never committed)
    └── 🎨 config.toml         # light wellness theme
```

Single-file by design — no framework soup, no build step.

---

## 🛠️ Tech stack

| Tech | Role |
|---|---|
| 🐍 Python 3.12 | All logic |
| 🎈 Streamlit 1.50 | Dashboard UI |
| 🐼 Pandas | Totals, tables, CSV export |
| 🌐 Requests | USDA + OpenFoodFacts calls |
| 🌿 USDA FoodData Central | Nutrient database (free, public domain CC0) |
| 🏷️ OpenFoodFacts | Barcode fallback |

---

## ❓ Troubleshooting

<details>
<summary><b>🔑 "USDA API key missing" banner</b></summary>
<br>

Add `[usda] api_key = "…"` to `.streamlit/secrets.toml` (or env `USDA_API_KEY`) and **restart** the app. Dashboard/CSV still work without it — only search is disabled.

</details>

<details>
<summary><b>🔍 No search results</b></summary>
<br>

Use short generic words: `banana`, `rice`, `chicken breast` — not sentences or brand slogans.

</details>

<details>
<summary><b>📷 Barcode not found</b></summary>
<br>

The app tries USDA Branded first, then OpenFoodFacts. Very new/local products may exist in neither — log them via food search instead.

</details>

<details>
<summary><b>🌗 Weird dark colors?</b></summary>
<br>

The app is designed for the **Light** theme (forced via `.streamlit/config.toml`). If you manually picked *Dark* in Streamlit's `⋮ → Settings → Theme`, switch it back to **Light** (or *System* with light OS mode) and reload.

</details>

---

## 🔮 Roadmap

- [ ] 📸 Photo food recognition
- [ ] 📈 Weekly trends & streaks
- [ ] 🤖 "What should I eat next?" suggestions
- [ ] 💾 Persistent history (SQLite)
- [ ] ⌚ Fitness-tracker sync

---

## 🎓 Academic context

Built as a **major academic project** for the **AICTE / Edunet Foundation SkillsBuild** program — exploring:

```text
API integration  +  data processing  +  interactive web apps
```

---

## 👩‍💻 Author

<div align="center">

**Akshaya Srutisri**
*Computer Science · AI · Computer Vision · Software Development*

[![GitHub](https://img.shields.io/badge/GitHub-Akshaya--Sruti-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Akshaya-Sruti)

</div>

---

## 📄 License

MIT — do anything cool with it, just keep the notice. See `LICENSE`.

<div align="center">

### 🥗 Eat. Track. Understand.

*Data: U.S. Department of Agriculture, Agricultural Research Service. FoodData Central (public domain, CC0).*

</div>
