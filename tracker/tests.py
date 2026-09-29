from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
import datetime

from .models import UserProfile, FoodItem, MealLog
from .ai_engine import calculate_nutrition_profile, get_ai_meal_suggestions, parse_natural_language_food_entry

class NutritionEngineTests(TestCase):
    def test_mifflin_st_jeor_bmr_male(self):
        # Male, 70kg, 175cm, 25yr
        # BMR = (10*70) + (6.25*175) - (5*25) + 5 = 700 + 1093.75 - 125 + 5 = 1673.75 -> 1673.8
        profile = calculate_nutrition_profile(
            weight_kg=70.0, height_cm=175.0, age=25, gender='male',
            activity_level='sedentary', fitness_goal='maintenance'
        )
        self.assertAlmostEqual(profile['bmr'], 1673.8, delta=1.0)
        self.assertEqual(profile['protein_ratio'], 0.8) # Sedentary maintenance is NIH RDA 0.8g/kg
        self.assertAlmostEqual(profile['daily_protein'], 56.0, delta=0.5)

    def test_hypertrophy_protein_targets(self):
        # Male, 80kg, muscle_gain -> 2.0g/kg
        profile = calculate_nutrition_profile(
            weight_kg=80.0, height_cm=180.0, age=28, gender='male',
            activity_level='moderate', fitness_goal='muscle_gain'
        )
        self.assertEqual(profile['protein_ratio'], 2.0)
        self.assertEqual(profile['daily_protein'], 160.0)
        self.assertEqual(profile['recommended_meals'], 4)
        self.assertEqual(profile['per_meal_protein'], 40.0)

    def test_who_fat_amdr_compliance(self):
        profile = calculate_nutrition_profile(
            weight_kg=75.0, height_cm=175.0, age=30, gender='male',
            activity_level='moderate', fitness_goal='maintenance'
        )
        total_calories = profile['daily_calories']
        fat_calories = profile['daily_fat'] * 9.0
        fat_percentage = (fat_calories / total_calories) * 100
        # WHO recommends total fats between 20% and 30% of energy
        self.assertTrue(20.0 <= fat_percentage <= 30.0)


class DatabaseAndAITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='password123')
        self.chicken = FoodItem.objects.create(
            name='Chicken Breast (Skinless, Grilled)',
            category='poultry_meat',
            calories_per_100g=Decimal('165.0'),
            protein_per_100g=Decimal('31.0'),
            carbs_per_100g=Decimal('0.0'),
            fat_per_100g=Decimal('3.6'),
            is_verified=True,
            usda_fdc_id='171077'
        )

    def test_protein_density(self):
        # (31g * 4 / 165) * 100 = 75.15%
        density = self.chicken.protein_density_percentage()
        self.assertAlmostEqual(density, 75.2, delta=0.5)

    def test_natural_language_parser(self):
        res = parse_natural_language_food_entry('200g chicken breast')
        self.assertIsNotNone(res)
        self.assertEqual(res['serving_g'], 200.0)
        self.assertEqual(res['protein_g'], 62.0)
        self.assertEqual(res['calories'], 330.0)

    def test_ai_suggestions_generation(self):
        suggestions = get_ai_meal_suggestions(
            target_protein=150.0,
            logged_protein=100.0,
            target_calories=2400.0,
            logged_calories=1800.0,
            dietary_pref='omnivore'
        )
        self.assertEqual(suggestions['status'], 'in_progress')
        self.assertEqual(suggestions['protein_deficit'], 50.0)
        self.assertTrue(len(suggestions['boosters']) > 0)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='demouser', password='demopassword')

    def test_public_pages_load(self):
        response_home = self.client.get('/')
        self.assertEqual(response_home.status_code, 200)

        response_calc = self.client.get('/calculator/')
        self.assertEqual(response_calc.status_code, 200)

        response_foods = self.client.get('/foods/')
        self.assertEqual(response_foods.status_code, 200)

    def test_demo_login_flow(self):
        response = self.client.get('/demo-login/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Daily Nutrition & Protein Tracker")
