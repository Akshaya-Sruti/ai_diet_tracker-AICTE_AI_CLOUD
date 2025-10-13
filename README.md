
# AI Diet Tracker 🥗

**AI Diet Tracker** is a Streamlit web application that helps users log their meals, track calories, and monitor macronutrients using natural language input or barcode scanning.  
This project was developed as a major submission for academic purposes.

---

## Features

1. **Natural-language meal input**  
   - Enter meals in plain English (e.g., `2 scrambled eggs, 1 slice toast, 1 apple`)  
   - Retrieves calories, protein, carbs, and fat using the **Nutritionix API**

2. **Barcode lookup for packaged foods**  
   - Enter a product barcode (EAN/UPC) to fetch nutritional information from **OpenFoodFacts API**

3. **Daily log and summary**  
   - View all meals added for the day  
   - See totals for calories, protein, carbs, and fat  
   - Export meal log as a CSV file

4. **Custom daily calorie target**  
   - Set your goal and track progress with a visual progress bar

---

## Tech Stack

- **Python 3.8+**  
- **Streamlit** – interactive web interface  
- **Pandas** – data handling  
- **Requests** – API calls

---

## APIs Used

1. **Nutritionix API**  
   - For analyzing meals entered in natural language  
   - Free tier available at [Nutritionix Developer Portal](https://developer.nutritionix.com/)  
   - Requires `APP_ID` and `APP_KEY`  

2. **OpenFoodFacts API**  
   - For barcode-based food lookup  
   - Free to use, no API key required  
   - Documentation: [OpenFoodFacts API](https://world.openfoodfacts.org/data)

---


## Setup & Installation (Local)

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/ai_diet_tracker.git
cd ai_diet_tracker
````

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

* **Windows:**

```bash
venv\Scripts\activate
```

* **macOS/Linux:**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up API keys

**Option A — Streamlit secrets (recommended)**
Create `.streamlit/secrets.toml`:

```toml
[nutritionix]
app_id = "YOUR_APP_ID"
app_key = "YOUR_APP_KEY"
```

**Option B — Environment variables**

```bash
setx NUTRITIONIX_APP_ID "YOUR_APP_ID"
setx NUTRITIONIX_APP_KEY "YOUR_APP_KEY"
```

---

### 6. Run the app

```bash
python -m streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`) to use the app.

---

## Usage Guide

1. Enter meals in natural language and click **Analyze & Add meal (NL)**
2. Or enter a barcode and click **Lookup barcode**
3. View your meal log, totals, and download as CSV
4. Set daily calorie goal to track progress

---


---

## Future Enhancements

* Image-based food recognition
* Weekly/monthly analytics and charts
* Integration with fitness tracker APIs
* Personalized meal suggestions based on calorie goals

---

## Short Project Report (Summary & Architecture)

**Project Objective:**
To create an AI-powered diet tracker that allows users to log meals in natural language or via barcode scanning, and automatically track calories and macros.

**System Architecture:**

1. **Frontend:** Streamlit app interface for meal input, barcode scanning, and visualization.
2. **Backend:** Python code using Requests to fetch nutrition data from APIs.
3. **Data Handling:** Pandas to store meals in memory and export CSV for user records.
4. **APIs:** Nutritionix API for natural language meal analysis, OpenFoodFacts API for barcode lookup.

**Key Functionalities:**

* Natural language parsing of meals
* Barcode lookup for packaged foods
* Daily nutrition summary and CSV export
* Progress tracking toward user-defined calorie goals

---

## License

This project is licensed under the MIT License.
You are free to use, modify, and distribute for educational purposes.



