from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import datetime

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary (Little or no exercise)'),
        ('light', 'Lightly Active (1-3 days/week)'),
        ('moderate', 'Moderately Active (3-5 days/week)'),
        ('very_active', 'Very Active (6-7 days/week)'),
        ('extra_active', 'Extra Active (Heavy training / physical labor)'),
    ]

    GOAL_CHOICES = [
        ('maintenance', 'Maintain Weight & Vitality'),
        ('muscle_gain', 'Build Muscle / Hypertrophy'),
        ('fat_loss', 'Fat Loss / Cutting (Preserve Lean Mass)'),
        ('endurance', 'Athletic Endurance & Performance'),
    ]

    DIET_PREFERENCES = [
        ('omnivore', 'Omnivore (All foods)'),
        ('vegetarian', 'Vegetarian (No meat/fish)'),
        ('vegan', 'Vegan (Strict plant-based)'),
        ('pescatarian', 'Pescatarian (Fish & plant-based)'),
        ('keto', 'Keto / Low-Carb'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField(default=26)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, default=70.0)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, default=175.0)
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='moderate')
    fitness_goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='muscle_gain')
    dietary_preference = models.CharField(max_length=20, choices=DIET_PREFERENCES, default='omnivore')

    # Target metrics computed based on profile and goal
    target_calories = models.PositiveIntegerField(default=2300)
    target_protein_g = models.DecimalField(max_digits=6, decimal_places=1, default=140.0)
    target_carbs_g = models.DecimalField(max_digits=6, decimal_places=1, default=260.0)
    target_fat_g = models.DecimalField(max_digits=6, decimal_places=1, default=65.0)

    updated_at = models.DateTimeField(auto_now=True)

    def calculate_bmr(self):
        """Mifflin-St Jeor Equation for Basal Metabolic Rate (BMR)"""
        w = float(self.weight_kg)
        h = float(self.height_cm)
        a = float(self.age)
        if self.gender == 'female':
            bmr = (10 * w) + (6.25 * h) - (5 * a) - 161
        else:
            bmr = (10 * w) + (6.25 * h) - (5 * a) + 5
        return round(bmr, 1)

    def calculate_tdee(self):
        """Total Daily Energy Expenditure based on Physical Activity Level"""
        multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'very_active': 1.725,
            'extra_active': 1.9,
        }
        mult = multipliers.get(self.activity_level, 1.55)
        return round(self.calculate_bmr() * mult)

    def calculate_targets(self):
        """
        Calculates macronutrient and caloric targets tailored to body metrics and fitness goals.
        """
        w = float(self.weight_kg)
        tdee = self.calculate_tdee()

        # 1. Protein Target (g/kg bodyweight)
        if self.fitness_goal == 'muscle_gain':
            protein_ratio = 2.0  # 1.6 - 2.2 g/kg for hypertrophy (NIH/ISSN)
            calorie_target = tdee + 300  # Lean surplus
        elif self.fitness_goal == 'fat_loss':
            protein_ratio = 2.2  # 1.8 - 2.4 g/kg to spare muscle during calorie deficit
            calorie_target = max(1200, tdee - 450)  # Moderate deficit
        elif self.fitness_goal == 'endurance':
            protein_ratio = 1.4  # 1.2 - 1.6 g/kg endurance athletes
            calorie_target = tdee + 150
        else:  # maintenance
            if self.activity_level == 'sedentary':
                protein_ratio = 0.8  # NIH baseline RDA
            else:
                protein_ratio = 1.2  # Active maintenance
            calorie_target = tdee

        protein_g = round(w * protein_ratio, 1)

        # 2. Fat Target (WHO recommends 20-30% of daily calories)
        fat_calories = calorie_target * 0.25
        fat_g = round(fat_calories / 9.0, 1)

        # 3. Carbohydrates Target (Remaining calories, within WHO 45-65% AMDR)
        protein_calories = protein_g * 4.0
        remaining_cals = calorie_target - protein_calories - fat_calories
        carbs_g = max(50.0, round(remaining_cals / 4.0, 1))

        if self.dietary_preference == 'keto':
            carbs_g = 35.0
            fat_calories = calorie_target - protein_calories - (carbs_g * 4.0)
            fat_g = round(fat_calories / 9.0, 1)

        return {
            'calories': int(calorie_target),
            'protein_g': Decimal(str(protein_g)),
            'fat_g': Decimal(str(fat_g)),
            'carbs_g': Decimal(str(carbs_g)),
            'protein_ratio': protein_ratio,
            'bmr': self.calculate_bmr(),
            'tdee': tdee
        }

    def save(self, *args, **kwargs):
        # Auto-compute scientific targets if set to defaults
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} Profile ({self.fitness_goal})"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)
        targets = profile.calculate_targets()
        profile.target_calories = targets['calories']
        profile.target_protein_g = targets['protein_g']
        profile.target_carbs_g = targets['carbs_g']
        profile.target_fat_g = targets['fat_g']
        profile.save()


class FoodItem(models.Model):
    CATEGORY_CHOICES = [
        ('poultry_meat', 'Poultry & Meat'),
        ('fish_seafood', 'Fish & Seafood'),
        ('dairy_eggs', 'Dairy & Eggs'),
        ('legumes_beans', 'Legumes, Beans & Lentils'),
        ('plant_protein', 'Tofu & Plant Proteins'),
        ('nuts_seeds', 'Nuts & Seeds'),
        ('grains_cereals', 'Grains & Cereals'),
        ('vegetables_fruits', 'Vegetables & Fruits'),
        ('supplements', 'Protein Powders & Supplements'),
        ('prepared_dishes', 'Prepared Dishes'),
    ]

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    calories_per_100g = models.DecimalField(max_digits=6, decimal_places=1)
    protein_per_100g = models.DecimalField(max_digits=5, decimal_places=1)
    carbs_per_100g = models.DecimalField(max_digits=5, decimal_places=1)
    fat_per_100g = models.DecimalField(max_digits=5, decimal_places=1)
    fiber_per_100g = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)

    serving_size_g = models.DecimalField(max_digits=6, decimal_places=1, default=100.0)
    serving_unit_name = models.CharField(max_length=60, default='100g (standard serving)')

    usda_fdc_id = models.CharField(max_length=50, blank=True, null=True, help_text="USDA FoodData Central Identifier")
    is_verified = models.BooleanField(default=True, help_text="Verified USDA FoodData item")
    dietary_tags = models.CharField(max_length=120, blank=True, help_text="Comma-separated tags e.g. vegan,vegetarian,high-protein")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.protein_per_100g}g P / 100g)"

    def protein_density_percentage(self):
        """Calculates protein percentage of calories: (protein_g * 4 / calories) * 100"""
        if self.calories_per_100g > 0:
            pct = (float(self.protein_per_100g) * 4.0 / float(self.calories_per_100g)) * 100
            return round(pct, 1)
        return 0.0


class MealLog(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack / Post-Workout'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_logs')
    food_item = models.ForeignKey(FoodItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='meal_logs')
    food_name = models.CharField(max_length=150)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    serving_amount_g = models.DecimalField(max_digits=6, decimal_places=1, default=100.0)

    # Recorded values for this specific log
    calories = models.DecimalField(max_digits=6, decimal_places=1)
    protein_g = models.DecimalField(max_digits=6, decimal_places=1)
    carbs_g = models.DecimalField(max_digits=6, decimal_places=1)
    fat_g = models.DecimalField(max_digits=6, decimal_places=1)

    logged_date = models.DateField(default=datetime.date.today)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.food_name} ({self.meal_type}) on {self.logged_date}"
