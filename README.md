# 🥗 AI Diet Tracker

<p align="center">
  <strong>Track what you eat. Understand what you consume.</strong>
</p>

<p align="center">
  An AI-powered nutrition tracking application that turns natural-language meals and product barcodes into actionable nutrition data.
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge\&logo=streamlit\&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data-150458?style=for-the-badge\&logo=pandas\&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Academic%20Project-blue?style=for-the-badge)

</p>

---

## ✨ What is AI Diet Tracker?

**AI Diet Tracker** is a Streamlit-based nutrition tracking application designed to make food logging simple.

Instead of manually searching through nutrition databases, users can:

* 🗣️ Describe a meal using natural language
* 🏷️ Look up packaged food using a barcode
* 📊 Track calories and macronutrients
* 🎯 Set a daily calorie target
* 📥 Export their nutrition history as CSV

The application connects to external nutrition APIs and transforms their responses into a simple, user-friendly dashboard.

---

## 🚀 Core Features

<details>
<summary><strong>🗣️ Natural-Language Meal Logging</strong></summary>

<br>

Enter food exactly as you would normally describe it.

```text
2 scrambled eggs, 1 slice toast, 1 apple
```

The application sends the description to the **Nutritionix API** and retrieves:

* Calories
* Protein
* Carbohydrates
* Fat

No manual nutrition lookup required.

</details>

<details>
<summary><strong>🏷️ Barcode Food Lookup</strong></summary>

<br>

Have a packaged food product?

Enter its **EAN/UPC barcode** and the application queries **OpenFoodFacts** to retrieve available nutritional information.

Useful for:

* Packaged foods
* Snacks
* Cereals
* Beverages
* Processed foods

</details>

<details>
<summary><strong>📊 Daily Nutrition Dashboard</strong></summary>

<br>

Track your daily intake in one place.

| Metric           | Tracked |
| ---------------- | :-----: |
| 🔥 Calories      |    ✅    |
| 💪 Protein       |    ✅    |
| 🍞 Carbohydrates |    ✅    |
| 🥑 Fat           |    ✅    |
| 🍽️ Meals        |    ✅    |

The application maintains the current day's meal log and calculates cumulative nutrition totals.

</details>

<details>
<summary><strong>🎯 Custom Calorie Goal</strong></summary>

<br>

Set your own daily calorie target and monitor progress using a visual progress indicator.

```text
Daily Goal
━━━━━━━━━━━━━━━━━━━━━━ 72%

1,440 / 2,000 kcal
```

</details>

<details>
<summary><strong>📥 CSV Export</strong></summary>

<br>

Export your meal records for further analysis or personal record keeping.

The exported data can be opened in:

* Microsoft Excel
* Google Sheets
* Pandas
* Other data-analysis tools

</details>

---

# 🧠 How It Works

```text
                         USER
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       Natural Language            Barcode Input
              │                         │
              ▼                         ▼
       Nutritionix API           OpenFoodFacts API
              │                         │
              └────────────┬────────────┘
                           ▼
                  Nutrition Data
                           │
                           ▼
                    Python Backend
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                 Pandas       Calculations
                    │             │
                    └──────┬──────┘
                           ▼
                  Streamlit Dashboard
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           Meal Log     Nutrition    CSV Export
                         Summary
```

---

# 🏗️ Architecture

### 1. Presentation Layer

**Streamlit**

Handles:

* User input
* Buttons and controls
* Nutrition dashboard
* Progress visualization
* CSV download

### 2. Application Layer

**Python**

Responsible for:

* Processing user input
* Calling APIs
* Parsing API responses
* Calculating daily totals
* Managing meal records

### 3. Data Layer

**Pandas**

Used for:

* Storing meal records
* Aggregating nutrition values
* Generating CSV exports

### 4. External Data Sources

| API           | Purpose                             |
| ------------- | ----------------------------------- |
| Nutritionix   | Natural-language nutrition analysis |
| OpenFoodFacts | Barcode-based product lookup        |

---

# 🛠️ Tech Stack

<div align="center">

| Technology                | Purpose                        |
| ------------------------- | ------------------------------ |
| 🐍 **Python**             | Core application logic         |
| 🎈 **Streamlit**          | Web application interface      |
| 🐼 **Pandas**             | Data processing                |
| 🌐 **Requests**           | API communication              |
| 🥗 **Nutritionix API**    | Natural-language food analysis |
| 🏷️ **OpenFoodFacts API** | Barcode lookup                 |

</div>

---

# 🔌 API Integration

## 🥗 Nutritionix

Nutritionix powers the natural-language meal analysis.

Example:

```text
Input:
2 scrambled eggs, 1 slice toast, 1 apple

        ↓

Nutritionix API

        ↓

Calories
Protein
Carbohydrates
Fat
```

🔗 [Nutritionix Developer Portal](https://developer.nutritionix.com/)

> Requires an `APP_ID` and `APP_KEY`.

---

## 🏷️ OpenFoodFacts

OpenFoodFacts is used for barcode-based food identification.

```text
EAN / UPC
   │
   ▼
OpenFoodFacts
   │
   ▼
Product Information
   │
   ├── Product Name
   ├── Calories
   ├── Protein
   ├── Carbohydrates
   └── Fat
```

🔗 [OpenFoodFacts Data](https://world.openfoodfacts.org/data)

No API key is required for basic access.

---

# 📂 Project Structure

```text
ai_diet_tracker/
│
├── app.py
├── requirements.txt
├── README.md
│
├── .streamlit/
│   └── secrets.toml
│
└── data/
    └── ...
```

---

# ⚡ Getting Started

## 1️⃣ Clone the repository

```bash
git clone https://github.com/Akshaya-Sruti/ai_diet_tracker-AICTE_AI_CLOUD.git
cd ai_diet_tracker-AICTE_AI_CLOUD
```

## 2️⃣ Create a virtual environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

---

## 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Configure Nutritionix

Create:

```text
.streamlit/secrets.toml
```

Add:

```toml
[nutritionix]
app_id = "YOUR_APP_ID"
app_key = "YOUR_APP_KEY"
```

### Alternative: Environment Variables

**Windows**

```bash
setx NUTRITIONIX_APP_ID "YOUR_APP_ID"
setx NUTRITIONIX_APP_KEY "YOUR_APP_KEY"
```

---

## 5️⃣ Launch the application

```bash
python -m streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

---

# 🧪 Usage

### 🥗 Option 1 — Log a Meal

Enter something like:

```text
2 eggs, 2 slices of toast and a banana
```

Click:

**Analyze & Add Meal**

The nutrition information is retrieved and added to your daily log.

---

### 🏷️ Option 2 — Scan a Product

Enter a barcode:

```text
8901234567890
```

Click:

**Lookup Barcode**

The application retrieves the available product nutrition information.

---

### 📊 Option 3 — Track Progress

Set your calorie target:

```text
Daily Goal → 2000 kcal
```

The dashboard calculates your current intake and displays progress toward the goal.

---

### 📥 Option 4 — Export

Download your meal history as a CSV file for external analysis.

---

# 🎯 Project Objective

> **To develop an accessible nutrition tracking system that reduces the effort required to manually record food intake by combining natural-language processing through nutrition APIs with barcode-based food identification.**

The project demonstrates the integration of:

```text
User Input
     ↓
API Integration
     ↓
Data Processing
     ↓
Nutrition Calculation
     ↓
Interactive Visualization
```

---

# 🔮 Future Enhancements

The current architecture can be extended with:

<details>
<summary>📸 Image-Based Food Recognition</summary>

Use computer vision to identify food from an uploaded image and estimate its nutritional information.

</details>

<details>
<summary>📈 Weekly & Monthly Analytics</summary>

Add historical dashboards showing:

* Calorie trends
* Macronutrient distribution
* Average daily intake
* Meal patterns
* Goal consistency

</details>

<details>
<summary>⌚ Fitness Tracker Integration</summary>

Integrate activity data from supported fitness platforms to compare:

```text
Calories Consumed
        vs
Calories Burned
```

</details>

<details>
<summary>🤖 Personalized Meal Suggestions</summary>

Generate meal recommendations based on:

* Calorie targets
* Macronutrient requirements
* Previous meals
* Dietary preferences

</details>

---

# 📚 Academic Context

This application was developed as a **major academic project submission** as part of the **AICTE / Edunet Foundation SkillsBuild program**.

### Project Focus

```text
Artificial Intelligence
        +
API Integration
        +
Data Processing
        +
Interactive Web Applications
```

---

# 🔐 Security Notes

API credentials should **never be committed to GitHub**.

Add the following to `.gitignore`:

```gitignore
.streamlit/secrets.toml
.env
venv/
__pycache__/
```

Use Streamlit secrets or environment variables for credentials.

---

# 📌 Current Scope

| Capability                   |   Status   |
| ---------------------------- | :--------: |
| Natural-language meal input  |      ✅     |
| Nutrition API integration    |      ✅     |
| Barcode lookup               |      ✅     |
| Daily meal tracking          |      ✅     |
| Macronutrient tracking       |      ✅     |
| Calorie goal                 |      ✅     |
| CSV export                   |      ✅     |
| Image food recognition       | 🔮 Planned |
| Historical analytics         | 🔮 Planned |
| Fitness integration          | 🔮 Planned |
| Personalized recommendations | 🔮 Planned |

---

# 👩‍💻 Author

<p align="center">

<strong>Akshaya Srutisri</strong>

<br>

Computer Science Engineering · AI · Computer Vision · Software Development

<br><br>

<a href="https://github.com/Akshaya-Sruti">
<img src="https://img.shields.io/badge/GitHub-Akshaya--Sruti-181717?style=for-the-badge&logo=github&logoColor=white">
</a>

</p>

---

# 📄 License

This project is licensed under the **MIT License**.

See the `LICENSE` file for details.

---

<p align="center">

### 🥗 Eat. Track. Understand.

<strong>AI Diet Tracker</strong>

</p>
