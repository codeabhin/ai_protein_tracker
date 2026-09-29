import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.models import UserProfile, FoodItem, MealLog

class Command(BaseCommand):
    help = 'Creates a demo user with realistic meal logs for instant testing'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username='demo', defaults={
            'first_name': 'Alex',
            'last_name': 'Morgan',
            'email': 'demo@example.com'
        })
        user.set_password('demo1234')
        user.save()

        # Update profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.age = 28
        profile.gender = 'male'
        profile.weight_kg = Decimal('75.0')
        profile.height_cm = Decimal('178.0')
        profile.activity_level = 'moderate'
        profile.fitness_goal = 'muscle_gain'
        profile.dietary_preference = 'omnivore'

        targets = profile.calculate_targets()
        profile.target_calories = targets['calories']
        profile.target_protein_g = targets['protein_g']
        profile.target_carbs_g = targets['carbs_g']
        profile.target_fat_g = targets['fat_g']
        profile.save()

        # Log some meals for today
        today = datetime.date.today()
        # Clean existing logs for today to avoid duplicates
        MealLog.objects.filter(user=user, logged_date=today).delete()

        # 1. Breakfast: Eggs & Rolled Oats
        egg = FoodItem.objects.filter(name__icontains='Whole Large Egg').first()
        if egg:
            MealLog.objects.create(
                user=user,
                food_item=egg,
                food_name=egg.name,
                meal_type='breakfast',
                serving_amount_g=Decimal('100.0'),  # 2 eggs
                calories=Decimal('155.0'),
                protein_g=Decimal('12.6'),
                carbs_g=Decimal('1.1'),
                fat_g=Decimal('10.6'),
                logged_date=today
            )

        oats = FoodItem.objects.filter(name__icontains='Rolled Oats').first()
        if oats:
            MealLog.objects.create(
                user=user,
                food_item=oats,
                food_name=oats.name,
                meal_type='breakfast',
                serving_amount_g=Decimal('60.0'),
                calories=Decimal('227.4'),
                protein_g=Decimal('7.9'),
                carbs_g=Decimal('40.6'),
                fat_g=Decimal('3.9'),
                logged_date=today
            )

        # 2. Lunch: Grilled Chicken Breast & Quinoa & Broccoli
        chicken = FoodItem.objects.filter(name__icontains='Chicken Breast').first()
        if chicken:
            MealLog.objects.create(
                user=user,
                food_item=chicken,
                food_name=chicken.name,
                meal_type='lunch',
                serving_amount_g=Decimal('180.0'),
                calories=Decimal('297.0'),
                protein_g=Decimal('55.8'),
                carbs_g=Decimal('0.0'),
                fat_g=Decimal('6.5'),
                logged_date=today
            )

        quinoa = FoodItem.objects.filter(name__icontains='Quinoa').first()
        if quinoa:
            MealLog.objects.create(
                user=user,
                food_item=quinoa,
                food_name=quinoa.name,
                meal_type='lunch',
                serving_amount_g=Decimal('150.0'),
                calories=Decimal('180.0'),
                protein_g=Decimal('6.6'),
                carbs_g=Decimal('32.0'),
                fat_g=Decimal('2.9'),
                logged_date=today
            )

        # 3. Afternoon Snack: Greek Yogurt
        yogurt = FoodItem.objects.filter(name__icontains='Greek Yogurt').first()
        if yogurt:
            MealLog.objects.create(
                user=user,
                food_item=yogurt,
                food_name=yogurt.name,
                meal_type='snack',
                serving_amount_g=Decimal('170.0'),
                calories=Decimal('100.3'),
                protein_g=Decimal('17.5'),
                carbs_g=Decimal('6.1'),
                fat_g=Decimal('0.7'),
                logged_date=today
            )

        self.stdout.write(self.style.SUCCESS("Demo user created successfully (Username: demo, Password: demo1234)"))
