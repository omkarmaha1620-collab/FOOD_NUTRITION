# Food Nutrition Analyzer

A functional, full-stack college mini project web application built with **Python Flask**, **MySQL**, **HTML5**, **CSS3**, and **JavaScript** (with **Chart.js**).

The application enables users to search for food items, calculate exact nutritional values based on portion sizes (quantity in grams), record and categorize meals across the day, track daily caloric and macronutrient intake, compute Body Mass Index (BMI), estimate daily calorie requirements using the Mifflin-St Jeor equation, generate visual progress reports, and manage food items through an administrative panel.

---

## 1. Project Objective

The primary objective of the **Food Nutrition Analyzer** is to provide an accessible, educational, and scientifically sound tool to help individuals understand their dietary habits. By breaking down food intake into measurable macronutrients (protein, carbohydrates, fats, dietary fiber) and calories based on portion weight, users gain actionable insights into their nutritional intake compared against standard estimated energy requirements.

---

## 2. System Flow

The complete user workflow is structured as follows:

```
[ User ]
   │
   ▼
[ 1. User Registration / Login ] ── (Password Hashing & Session Setup)
   │
   ▼
[ 2. Profile Setup ] ────────────── (Age, Gender, Height cm, Weight kg, Activity Level)
   │
   ▼
[ 3. Health Assessment ] ────────── (BMI Calculation & Mifflin-St Jeor Calorie Target)
   │
   ▼
[ 4. Food Search & Selection ] ──── (Filter 45+ items across 9 categories)
   │
   ▼
[ 5. Enter Quantity (Grams) ] ───── (Live scaling: (Nutrient / 100) * Grams)
   │
   ▼
[ 6. Add to Meal Diary ] ────────── (Breakfast / Lunch / Dinner / Snacks)
   │
   ▼
[ 7. Daily Tracking & Dashboard ] ─ (Intake vs Target, Remaining Calories, Macro Progress)
   │
   ▼
[ 8. Nutrition Reports ] ────────── (Chart.js Trends, Macronutrient Ratios, Print / Export)
```

---

## 3. Technology Stack & Rationale

| Layer | Technology | Rationale / Viva Explanation |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6) | Responsive, lightweight, standards-compliant user interface without heavy frontend frameworks. |
| **Styling** | Bootstrap 5.3 & Custom CSS | Clean, modern cards, progress bars, responsive navigation, and `@media print` print styling. |
| **Charts** | Chart.js 4.4 | Client-side Canvas-based rendering for calorie intake trends and macronutrient donut charts. |
| **Backend** | Python Flask (3.x) | Lightweight WSGI web framework, modular routing, Jinja2 templating, and session management. |
| **Database** | MySQL (with PyMySQL) | Relational database management system with foreign keys, constraints, and ACID compliance. |
| **Security** | Werkzeug Security (scrypt) | Salted password hashing to protect user and admin credentials. Parameterized SQL queries prevent SQL Injection. |

---

## 4. System Modules Breakdown (12 Modules)

### Module 1: User Registration and Login
- Registration collects full name, email, password, age, gender, height (cm), weight (kg), and activity level.
- Passwords are encrypted using salted `scrypt` hashing (`werkzeug.security`).
- Secure session-based authentication (`session['user_id']`).
- Client-side and server-side form validation (positive numerical ranges, email formatting).

### Module 2: User Profile
- Displays and allows updating of physical metrics: Name, Age, Gender, Height, Weight, Activity Level.
- Dynamic recalculation of BMI and daily calorie goals upon profile update.

### Module 3: Food Database
- Normalized MySQL table `food_items` storing nutritional metrics **per 100 grams** (Calories, Protein, Carbohydrates, Fat, Fiber, Serving Size, Micronutrients).
- Includes 45+ pre-seeded food items covering 9 distinct categories:
  - Fruits, Vegetables, Grains, Pulses, Dairy, Eggs, Meat/Fish, Snacks, and Beverages.

### Module 4: Food Search
- Interactive search page with real-time client-side keyword filtering and server-side category filters.
- Displays standard serving sizes and per-100g nutritional facts.

### Module 5: Quantity-Based Nutrition Calculation
- Computes exact nutrient consumption scaled to grams:
  $$\text{Nutrient Consumed} = \frac{\text{Nutrient per 100g} \times \text{Quantity in Grams}}{100}$$
- Real-time client-side calculation before adding the item to the meal diary.
- REST API endpoint (`/api/calculate-nutrition`) returning JSON for programmatic consumption.

### Module 6: Meal Management
- Users can assign foods to four standard meal types:
  - **Breakfast**, **Lunch**, **Dinner**, **Snacks**.
- Records timestamp, user ID, food ID, gram quantity, and calculated nutritional values.
- Full CRUD: Users can add items, edit portion sizes (with automatic recalculation), and delete entries.

### Module 7: Daily Nutrition Tracking
- Interactive calendar date selector with Previous Day / Next Day navigation.
- Groups entries by meal type with sub-totals and daily grand totals.
- Displays consumed totals alongside target values.

### Module 8: BMI Calculator
- Computes Body Mass Index:
  $$\text{BMI} = \frac{\text{Weight (kg)}}{(\text{Height in meters})^2}$$
- Evaluates standard WHO categories:
  - **Underweight**: BMI < 18.5
  - **Normal weight**: 18.5 ≤ BMI ≤ 24.9
  - **Overweight**: 25.0 ≤ BMI ≤ 29.9
  - **Obesity**: BMI ≥ 30.0
- Includes clear health guidance and an explicit disclaimer that BMI is a general screening indicator, not a medical diagnosis.

### Module 9: Daily Calorie Requirement
- Estimates Basal Metabolic Rate (BMR) using the scientifically recognized **Mifflin-St Jeor Equation**:
  - **Men**: $\text{BMR} = 10 \times W + 6.25 \times H - 5 \times A + 5$
  - **Women**: $\text{BMR} = 10 \times W + 6.25 \times H - 5 \times A - 161$
- Applies physical activity multipliers:
  - **Sedentary**: $\times 1.2$
  - **Lightly Active**: $\times 1.375$
  - **Moderately Active**: $\times 1.55$
  - **Very Active**: $\times 1.725$
  - **Extra Active**: $\times 1.9$
- Displays Total Daily Energy Expenditure (TDEE) and recommended macronutrient distribution (Protein 20%, Carbs 50%, Fat 30%).

### Module 10: Nutrition Dashboard
- Displays calories consumed vs daily target vs calories remaining with color-coded progress indicators.
- Macro summary cards for Protein, Carbohydrates, Fat, and Dietary Fiber.
- Quick BMI widget with scale bar.
- Meal overview breakdown cards for Breakfast, Lunch, Dinner, and Snacks.

### Module 11: Reports & Visualization
- Multi-period filtering: Today, Specific Date, or Last 7 Days (Weekly Summary).
- Data visualizations with Chart.js:
  - Daily Calorie Intake Trend (Bar chart)
  - Macronutrient Proportion (Doughnut chart)
- Printable / downloadable report mode with custom print stylesheet (`@media print`).

### Module 12: Admin Panel
- Dedicated administrator login portal (`/admin/login`).
- System statistics: Total users, food count, total meal entries.
- Registered users list (ID, Name, Email, Age, Gender, Activity Level, Registration Date, Meals Logged).
- Food database management with complete CRUD operations (Add food, Edit food, Delete food).
- Restricted access enforced via `@admin_required` authorization decorator.

---

## 5. Database Design & Tables

The database schema (`food_nutrition_db`) is defined in `database.sql`:

```
┌───────────────────────┐             ┌─────────────────────────┐
│         users         │             │       food_items        │
├───────────────────────┤             ├─────────────────────────┤
│ id (PK)               │◄──────┐     │ id (PK)                 │◄──────┐
│ name                  │       │     │ name                    │       │
│ email (UNIQUE)        │       │     │ category                │       │
│ password_hash         │       │     │ serving_size            │       │
│ age                   │       │     │ calories_per_100g       │       │
│ gender                │       │     │ protein_per_100g        │       │
│ height_cm             │       │     │ carbs_per_100g          │       │
│ weight_kg             │       │     │ fat_per_100g            │       │
│ activity_level        │       │     │ fiber_per_100g          │       │
│ created_at            │       │     │ micronutrients          │       │
└───────────────────────┘       │     │ created_at              │       │
                                │     └─────────────────────────┘       │
                                │                                       │
                    ┌───────────┴─────────────┐                         │
                    │      meal_entries       │                         │
                    ├─────────────────────────┤                         │
                    │ id (PK)                 │                         │
                    │ user_id (FK -> users)   │                         │
                    │ food_id (FK -> foods)   │─────────────────────────┘
                    │ meal_type               │
                    │ quantity_grams          │
                    │ calories                │
                    │ protein, carbs, fat     │
                    │ fiber                   │
                    │ entry_date              │
                    │ created_at              │
                    └─────────────────────────┘

┌───────────────────────┐
│        admins         │
├───────────────────────┤
│ id (PK)               │
│ username (UNIQUE)     │
│ email (UNIQUE)        │
│ password_hash         │
│ full_name             │
│ created_at            │
└───────────────────────┘
```

---

## 6. How to Set Up and Run

### Step 1: Clone or Navigate to Directory
```bash
cd c:\FOOD_NUTRITION
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Database Settings
Edit `.env` (or copy from `.env.example`) and provide your MySQL root password:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_NAME=food_nutrition_db
SECRET_KEY=food_nutrition_analyzer_secure_key_2026
PORT=5000
```

### Step 4: Initialize the Database
Run the automated initialization script to create the database, tables, and 45+ seed foods:
```bash
python init_db.py
```
*(Alternatively, import `database.sql` directly into MySQL Workbench or MySQL CLI: `mysql -u root -p < database.sql`)*.

> **Note on Dual-Engine Fallback:** If MySQL credentials are not yet configured, the system automatically uses an embedded SQLite database (`food_nutrition.db`) pre-populated with identical schema and data, allowing immediate project demonstration.

### Step 5: Start the Web Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 7. Demo Accounts for Evaluation

| Role | Username / Email | Password | Access Portal |
| :--- | :--- | :--- | :--- |
| **Demo User** | `john@example.com` | `User@123` | `/login` |
| **Administrator** | `admin@nutrition.com` | `Rakshitha@456` | `/admin/login` |

---

## 8. Common College Viva Questions & Model Answers

### Q1: Why did you choose Python Flask for the backend?
**Answer:** Flask is a micro-framework that gives precise control over the application architecture. It is lightweight, does not enforce unnecessary boilerplate like Django, allows clean separation between routing (`app.py`), database execution (`db.py`), and mathematical calculations (`nutrition_calc.py`), and integrates directly with Jinja2 templates.

### Q2: How is SQL Injection prevented in this application?
**Answer:** SQL Injection is prevented by using **parameterized queries** with placeholders (`%s`). User inputs are passed as separate parameter tuples to PyMySQL's cursor execution (`cursor.execute(sql, params)`), ensuring the database engine compiles the SQL query structure before inserting the values as literal data rather than executable code.

### Q3: How do you handle password security?
**Answer:** Passwords are never stored as plain text. When a user registers, Werkzeug's `generate_password_hash` hashes the password using the salted **scrypt** cryptographic hashing algorithm. During login, `check_password_hash` compares the candidate password against the stored hash without ever needing to decrypt it.

### Q4: Explain the Quantity-Based Nutrition Formula.
**Answer:** Standard nutritional databases store nutritional values per 100 grams of food. If a user consumes $Q$ grams of a food with $N$ amount of a nutrient per 100g, the nutrient consumed is:
$$\text{Nutrient Consumed} = \frac{N \times Q}{100}$$
For example, Cooked White Rice has 130 kcal per 100g. Consuming 200g yields:
$$\frac{130 \times 200}{100} = 260\text{ kcal}$$

### Q5: How is BMI calculated and categorized?
**Answer:** Body Mass Index is calculated as:
$$\text{BMI} = \frac{\text{Weight in kg}}{(\text{Height in meters})^2}$$
Height is converted from centimeters to meters ($H_m = H_{cm} / 100$). Standard WHO categories are: Underweight (< 18.5), Normal weight (18.5–24.9), Overweight (25–29.9), and Obesity (≥ 30.0). We also explicitly state that BMI is a general screening indicator rather than a medical diagnosis.

### Q6: What equation is used for Daily Calorie Estimation?
**Answer:** We use the **Mifflin-St Jeor Equation** to calculate Basal Metabolic Rate (BMR), which scientific literature recognizes as one of the most accurate equations for healthy individuals:
- Men: $10 \times \text{weight (kg)} + 6.25 \times \text{height (cm)} - 5 \times \text{age} + 5$
- Women: $10 \times \text{weight (kg)} + 6.25 \times \text{height (cm)} - 5 \times \text{age} - 161$
We then multiply BMR by an activity factor (from 1.2 for sedentary to 1.9 for extra active) to estimate Total Daily Energy Expenditure (TDEE).
