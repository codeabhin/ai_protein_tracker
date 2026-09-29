# AI Protein Intake Calculator and Diet Food Tracking System

A full-stack web application built with **Python 3**, **Django**, **HTML5**, **CSS3**, and **SQLite** designed to calculate personalized daily protein targets and track daily meals with precision.

---

## 🌟 Key Features

- **AI Protein & Macro Calculator**:
  - Computes Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE).
  - Calculates daily protein requirement based on your body weight, activity level, and fitness goals (muscle hypertrophy, fat loss, or maintenance).
  - Provides optimal per-meal protein distribution pacing and daily hydration goals.
- **AI Smart Deficit Closer & Meal Recommender**:
  - Real-time recommendation heuristics monitor your logged meals and compute remaining protein and calorie deficits.
  - Suggests tailored, high-protein food options to hit your targets without overshooting calories.
- **Natural Language Quick Food Logger**:
  - Type entries like `"200g chicken breast"`, `"2 large eggs"`, or `"1 scoop whey protein"`.
  - Intelligently parses portions and matches against the food database.
- **Interactive Daily Dashboard & Visual Analytics**:
  - Real-time progress bars for Protein, Calories, Carbs, and Fats.
  - 7-Day historical protein tracking bar chart via Chart.js.
  - Daily macronutrient distribution breakdown chart.
  - Breakfast, Lunch, Dinner, and Snack journals with instant one-click deletion and modal additions.
- **Rich Food Database**:
  - Searchable by keyword, filterable by food group (Poultry & Meat, Fish & Seafood, Dairy, Legumes, Plant Protein, Grains, Supplements) and sortable by protein density.
- **Authentication & 1-Click Demo Mode**:
  - Full registration and login system with user profiles.
  - Built-in `demo` account pre-populated with realistic daily meals.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.9+, Django 4.2 LTS
- **Database**: SQLite3 (embedded relational database)
- **Frontend**: HTML5, Semantic UI, Custom CSS3 Variables & Flexbox/Grid, Vanilla JavaScript
- **Data Visualization**: Chart.js 4.4

---

## 🚀 Quickstart Guide

### 1. Activate Virtual Environment
```bash
cd /Users/abhinj/.gemini/antigravity/scratch/ai_protein_tracker
source venv/bin/activate
```

### 2. Run Database Migrations (SQLite)
```bash
python manage.py migrate
```

### 3. Seed Food Database & Demo User
```bash
python manage.py seed_foods
python manage.py seed_demo_user
```

### 4. Run the Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your web browser.

### 5. Instant Demo Credentials
- **Username**: `demo`
- **Password**: `demo1234`
*(Or click the **🚀 Instant Demo** button in the navbar for immediate 1-click access)*

### 6. Run Test Suite
```bash
python manage.py test
```
