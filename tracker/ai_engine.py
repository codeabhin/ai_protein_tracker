"""
AI Nutrition & Macro Calculator Engine
Computes BMR, TDEE, optimal daily protein, carbs, fats, 
and meal-by-meal distribution tailored to fitness and physique goals.
"""

import re
from decimal import Decimal
from .models import FoodItem

def calculate_nutrition_profile(weight_kg, height_cm, age, gender, activity_level, fitness_goal, dietary_pref='omnivore'):
    """
    Computes precise BMR, TDEE, optimal daily protein, carbs, fats, 
    and meal-by-meal distribution based on body composition and training targets.
    """
    w = float(weight_kg)
    h = float(height_cm)
    a = float(age)

    # 1. BMR via Mifflin-St Jeor formula
    if gender.lower() == 'female':
        bmr = (10 * w) + (6.25 * h) - (5 * a) - 161
    else:
        bmr = (10 * w) + (6.25 * h) - (5 * a) + 5
    bmr = round(bmr, 1)

    # 2. Activity Multipliers
    activity_factors = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'very_active': 1.725,
        'extra_active': 1.9,
    }
    factor = activity_factors.get(activity_level, 1.55)
    tdee = round(bmr * factor)

    # 3. Protein Target based on NIH & ISSN Scientific Recommendations
    # - NIH RDA baseline: 0.8 g/kg for sedentary adults
    # - ISSN / NIH sports recommendations: 1.4-2.0 g/kg for active/hypertrophy
    # - Deficit/cutting: 2.0-2.4 g/kg to prevent sarcopenia/muscle wasting
    if fitness_goal == 'muscle_gain':
        protein_ratio = 2.0
        caloric_adjustment = 300  # Lean surplus for hypertrophy
        goal_summary = "Caloric surplus with high protein (2.0 g/kg) to maximize muscle protein synthesis (MPS)."
    elif fitness_goal == 'fat_loss':
        protein_ratio = 2.2
        caloric_adjustment = -450  # Moderate sustainable deficit
        goal_summary = "Hypocaloric diet with elevated protein (2.2 g/kg) to preserve lean mass during fat loss."
    elif fitness_goal == 'endurance':
        protein_ratio = 1.4
        caloric_adjustment = 150
        goal_summary = "Optimized protein (1.4 g/kg) for mitochondrial repair and cellular adaptation."
    else:  # maintenance
        if activity_level == 'sedentary':
            protein_ratio = 0.8  # NIH baseline
        else:
            protein_ratio = 1.2
        caloric_adjustment = 0
        goal_summary = "Balanced maintenance intake ensuring nitrogen equilibrium and optimal metabolic health."

    daily_calories = max(1200, tdee + caloric_adjustment)
    daily_protein = round(w * protein_ratio, 1)

    # 4. Fat calculation (WHO: 20-30% of total energy intake, saturated fat <10%)
    if dietary_pref == 'keto':
        daily_carbs = 35.0
        protein_cals = daily_protein * 4.0
        fat_cals = max(0, daily_calories - protein_cals - (daily_carbs * 4.0))
        daily_fat = round(fat_cals / 9.0, 1)
    else:
        fat_cals = daily_calories * 0.25  # 25% of calories
        daily_fat = round(fat_cals / 9.0, 1)
        # 5. Carbohydrate calculation (WHO AMDR 45-65%)
        protein_cals = daily_protein * 4.0
        carb_cals = max(0, daily_calories - protein_cals - fat_cals)
        daily_carbs = round(carb_cals / 4.0, 1)

    # 6. Protein Pacing & Timing (Muscle Protein Synthesis / MPS)
    # Research indicates 3-4 boluses of 0.40g/kg (25-45g) maximize MPS.
    meals_count = 4
    per_meal_protein = round(daily_protein / meals_count, 1)

    # WHO hydration estimate (approx 35 ml per kg body weight)
    daily_water_liters = round((w * 35) / 1000, 1)

    return {
        'bmr': bmr,
        'tdee': tdee,
        'daily_calories': daily_calories,
        'daily_protein': daily_protein,
        'daily_carbs': daily_carbs,
        'daily_fat': daily_fat,
        'protein_ratio': protein_ratio,
        'goal_summary': goal_summary,
        'per_meal_protein': per_meal_protein,
        'recommended_meals': meals_count,
        'daily_water_liters': daily_water_liters,
        'macro_percentages': {
            'protein': round((daily_protein * 4 / daily_calories) * 100),
            'carbs': round((daily_carbs * 4 / daily_calories) * 100),
            'fat': round((daily_fat * 9 / daily_calories) * 100),
        }
    }


def get_ai_meal_suggestions(target_protein, logged_protein, target_calories, logged_calories, dietary_pref='omnivore'):
    """
    Intelligent recommendation engine: analyzes protein and calorie gaps,
    and returns tailored food item combinations from the USDA database.
    """
    protein_deficit = max(0.0, float(target_protein) - float(logged_protein))
    calorie_deficit = max(0.0, float(target_calories) - float(logged_calories))

    # Base queryset filtered by dietary restrictions
    foods = FoodItem.objects.all()

    if dietary_pref == 'vegan':
        foods = foods.filter(dietary_tags__icontains='vegan')
    elif dietary_pref == 'vegetarian':
        foods = foods.filter(dietary_tags__icontains='vegetarian')
    elif dietary_pref == 'pescatarian':
        foods = foods.exclude(category='poultry_meat')
    elif dietary_pref == 'keto':
        foods = foods.filter(carbs_per_100g__lte=6.0)

    # Sort candidates by protein density: (protein * 4 / calories)
    candidates = list(foods)

    suggestions = []
    if protein_deficit <= 5:
        return {
            'status': 'achieved',
            'headline': 'Goal Met! Excellent Work.',
            'message': f"You've logged {logged_protein}g of protein today, reaching your daily target! Maintain hydration and rest for recovery.",
            'items': []
        }

    # Generate smart combination options
    # Option 1: Fast single high-protein booster
    single_boosters = []
    for food in candidates:
        if food.protein_per_100g > 0:
            # grams needed to satisfy remaining protein
            grams_needed = round((protein_deficit / float(food.protein_per_100g)) * 100)
            if 30 <= grams_needed <= 350:
                food_cals = round((float(food.calories_per_100g) * grams_needed) / 100)
                single_boosters.append({
                    'food': food,
                    'serving_g': grams_needed,
                    'protein': round(protein_deficit, 1),
                    'calories': food_cals,
                    'carb': round((float(food.carbs_per_100g) * grams_needed) / 100, 1),
                    'fat': round((float(food.fat_per_100g) * grams_needed) / 100, 1),
                })
    # Pick top 3 most calorie-efficient boosters
    single_boosters.sort(key=lambda x: x['calories'])

    # Option 2: High biological value (HBV) meal idea
    hbv_items = [b for b in single_boosters if b['food'].category in ['poultry_meat', 'fish_seafood', 'dairy_eggs', 'plant_protein', 'supplements']]

    insights = []
    if protein_deficit > 40:
        insights.append(f"You have a significant protein gap of {protein_deficit:.1f}g remaining. Consider splitting this over your next two meals.")
    else:
        insights.append(f"You're just {protein_deficit:.1f}g away from hitting today's target. A single high-protein snack will close this gap.")

    if calorie_deficit < (protein_deficit * 4):
        insights.append("Your calorie budget is tight. Prioritize lean protein isolates, egg whites, or white fish to hit your target without excess calories.")

    return {
        'status': 'in_progress',
        'protein_deficit': round(protein_deficit, 1),
        'calorie_deficit': round(calorie_deficit, 1),
        'headline': f"AI Diet Recommendation: Bridge Your {protein_deficit:.1f}g Protein Gap",
        'insights': insights,
        'boosters': single_boosters[:4]
    }


def parse_natural_language_food_entry(query):
    """
    Intelligent text parser: interprets strings like:
    - '200g chicken breast'
    - '2 large eggs'
    - '1 scoop whey protein'
    - '150g greek yogurt'
    Matches against FoodItem database with calculated macros.
    """
    clean_query = query.strip().lower()
    if not clean_query:
        return None

    # Check for grams pattern: e.g. "150g" or "150 g"
    gram_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:g|grams?)\b', clean_query)
    # Check for count pattern: e.g. "2 eggs" or "1 scoop"
    count_match = re.search(r'^(\d+(?:\.\d+)?)\s+([a-zA-Z\s]+)', clean_query)

    serving_g = 100.0  # default
    matched_food = None
    search_term = clean_query

    if gram_match:
        serving_g = float(gram_match.group(1))
        # Remove the gram token to get food name
        search_term = re.sub(r'(\d+(?:\.\d+)?)\s*(?:g|grams?)\b', '', clean_query).strip()
    elif count_match:
        quantity = float(count_match.group(1))
        unit_or_name = count_match.group(2).strip()
        search_term = unit_or_name
        # Some heuristics for counts
        if 'egg' in unit_or_name:
            serving_g = quantity * 50.0  # 1 egg ~ 50g
        elif 'scoop' in unit_or_name or 'shake' in unit_or_name:
            serving_g = quantity * 30.0  # 1 scoop ~ 30g
        elif 'cup' in unit_or_name:
            serving_g = quantity * 200.0
        elif 'can' in unit_or_name:
            serving_g = quantity * 165.0
        else:
            serving_g = quantity * 100.0

    # Search food in database
    words = [w for w in search_term.split() if len(w) > 2]
    best_match = None
    if words:
        qs = FoodItem.objects.all()
        for w in words:
            candidate = qs.filter(name__icontains=w).first()
            if candidate:
                best_match = candidate
                break

    if best_match:
        factor = serving_g / 100.0
        return {
            'food_id': best_match.id,
            'name': best_match.name,
            'serving_g': round(serving_g, 1),
            'protein_g': round(float(best_match.protein_per_100g) * factor, 1),
            'carbs_g': round(float(best_match.carbs_per_100g) * factor, 1),
            'fat_g': round(float(best_match.fat_per_100g) * factor, 1),
            'calories': round(float(best_match.calories_per_100g) * factor, 1),
            'category': best_match.get_category_display(),
            'source': 'Verified Database' if best_match.is_verified else 'Custom'
        }
    
    return None
