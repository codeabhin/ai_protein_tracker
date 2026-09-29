import datetime
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum

from .models import UserProfile, FoodItem, MealLog
from .forms import UserRegistrationForm, UserProfileForm, MealLogForm, CustomFoodForm
from .ai_engine import (
    calculate_nutrition_profile,
    get_ai_meal_suggestions,
    parse_natural_language_food_entry
)


def home_view(request):
    """Landing page featuring live guest calculator, system highlights, and quick demo link."""
    # Pre-calculated sample data for quick display
    featured_foods = FoodItem.objects.filter(is_verified=True).order_by('-protein_per_100g')[:6]
    return render(request, 'tracker/home.html', {
        'featured_foods': featured_foods,
    })


@login_required
def dashboard_view(request):
    """Daily tracking dashboard with macro rings, meal logs, weekly trends, and AI recommendations."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Date handling (default to today)
    date_str = request.GET.get('date')
    if date_str:
        try:
            current_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = datetime.date.today()
    else:
        current_date = datetime.date.today()

    prev_date = current_date - datetime.timedelta(days=1)
    next_date = current_date + datetime.timedelta(days=1)
    is_today = (current_date == datetime.date.today())

    # Get meal logs for the current date
    logs = MealLog.objects.filter(user=request.user, logged_date=current_date)

    # Group by meal category
    breakfast_logs = logs.filter(meal_type='breakfast')
    lunch_logs = logs.filter(meal_type='lunch')
    dinner_logs = logs.filter(meal_type='dinner')
    snack_logs = logs.filter(meal_type='snack')

    # Aggregations
    totals = logs.aggregate(
        total_cals=Sum('calories'),
        total_p=Sum('protein_g'),
        total_c=Sum('carbs_g'),
        total_f=Sum('fat_g')
    )

    logged_calories = round(float(totals['total_cals'] or 0), 1)
    logged_protein = round(float(totals['total_p'] or 0), 1)
    logged_carbs = round(float(totals['total_c'] or 0), 1)
    logged_fat = round(float(totals['total_f'] or 0), 1)

    target_calories = float(profile.target_calories)
    target_protein = float(profile.target_protein_g)
    target_carbs = float(profile.target_carbs_g)
    target_fat = float(profile.target_fat_g)

    # Progress percentages
    protein_pct = min(100, round((logged_protein / target_protein * 100) if target_protein > 0 else 0))
    calories_pct = min(100, round((logged_calories / target_calories * 100) if target_calories > 0 else 0))
    carbs_pct = min(100, round((logged_carbs / target_carbs * 100) if target_carbs > 0 else 0))
    fat_pct = min(100, round((logged_fat / target_fat * 100) if target_fat > 0 else 0))

    # Remaining balances
    remaining_protein = max(0.0, round(target_protein - logged_protein, 1))
    remaining_calories = max(0.0, round(target_calories - logged_calories, 1))

    # AI Smart Recommendations
    ai_suggestions = get_ai_meal_suggestions(
        target_protein=target_protein,
        logged_protein=logged_protein,
        target_calories=target_calories,
        logged_calories=logged_calories,
        dietary_pref=profile.dietary_preference
    )

    # Weekly history (past 7 days) for Chart.js
    history_labels = []
    history_protein = []
    history_calories = []
    today = datetime.date.today()
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_logs = MealLog.objects.filter(user=request.user, logged_date=day)
        day_p = day_logs.aggregate(s=Sum('protein_g'))['s'] or 0
        day_cal = day_logs.aggregate(s=Sum('calories'))['s'] or 0
        history_labels.append(day.strftime('%a %d'))
        history_protein.append(float(day_p))
        history_calories.append(float(day_cal))

    # Available foods for dropdown logging
    all_foods = FoodItem.objects.all().order_by('category', 'name')

    context = {
        'profile': profile,
        'current_date': current_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'is_today': is_today,
        'breakfast_logs': breakfast_logs,
        'lunch_logs': lunch_logs,
        'dinner_logs': dinner_logs,
        'snack_logs': snack_logs,
        'logged_calories': logged_calories,
        'logged_protein': logged_protein,
        'logged_carbs': logged_carbs,
        'logged_fat': logged_fat,
        'target_calories': target_calories,
        'target_protein': target_protein,
        'target_carbs': target_carbs,
        'target_fat': target_fat,
        'protein_pct': protein_pct,
        'calories_pct': calories_pct,
        'carbs_pct': carbs_pct,
        'fat_pct': fat_pct,
        'remaining_protein': remaining_protein,
        'remaining_calories': remaining_calories,
        'ai_suggestions': ai_suggestions,
        'all_foods': all_foods,
        'history_labels_json': json.dumps(history_labels),
        'history_protein_json': json.dumps(history_protein),
        'history_calories_json': json.dumps(history_calories),
    }
    return render(request, 'tracker/dashboard.html', context)


def calculator_view(request):
    """
    Dedicated AI Protein Intake & Diet Macro Calculator.
    Runs scientific formulas (Mifflin-St Jeor, WHO AMDR, NIH protein RDA/ISSN).
    """
    profile = None
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)

    # Initial form defaults from user profile or standard adult
    initial_data = {
        'weight_kg': float(profile.weight_kg) if profile else 70.0,
        'height_cm': float(profile.height_cm) if profile else 175.0,
        'age': profile.age if profile else 26,
        'gender': profile.gender if profile else 'male',
        'activity_level': profile.activity_level if profile else 'moderate',
        'fitness_goal': profile.fitness_goal if profile else 'muscle_gain',
        'dietary_preference': profile.dietary_preference if profile else 'omnivore',
    }

    result = None
    if request.method == 'POST':
        weight = float(request.POST.get('weight_kg', 70))
        height = float(request.POST.get('height_cm', 175))
        age = int(request.POST.get('age', 26))
        gender = request.POST.get('gender', 'male')
        activity = request.POST.get('activity_level', 'moderate')
        goal = request.POST.get('fitness_goal', 'muscle_gain')
        diet = request.POST.get('dietary_preference', 'omnivore')

        result = calculate_nutrition_profile(
            weight_kg=weight,
            height_cm=height,
            age=age,
            gender=gender,
            activity_level=activity,
            fitness_goal=goal,
            dietary_pref=diet
        )

        # Update initial_data with submitted values
        initial_data.update({
            'weight_kg': weight,
            'height_cm': height,
            'age': age,
            'gender': gender,
            'activity_level': activity,
            'fitness_goal': goal,
            'dietary_preference': diet,
        })

        # Option to save to profile if user requested
        if request.user.is_authenticated and 'save_to_profile' in request.POST:
            profile = request.user.profile
            profile.weight_kg = Decimal(str(weight))
            profile.height_cm = Decimal(str(height))
            profile.age = age
            profile.gender = gender
            profile.activity_level = activity
            profile.fitness_goal = goal
            profile.dietary_preference = diet
            profile.target_calories = result['daily_calories']
            profile.target_protein_g = Decimal(str(result['daily_protein']))
            profile.target_carbs_g = Decimal(str(result['daily_carbs']))
            profile.target_fat_g = Decimal(str(result['daily_fat']))
            profile.save()
            messages.success(request, "Your AI-calculated nutrition targets have been saved to your profile!")
            return redirect('dashboard')
    else:
        # Default computation on initial page load
        result = calculate_nutrition_profile(
            weight_kg=initial_data['weight_kg'],
            height_cm=initial_data['height_cm'],
            age=initial_data['age'],
            gender=initial_data['gender'],
            activity_level=initial_data['activity_level'],
            fitness_goal=initial_data['fitness_goal'],
            dietary_pref=initial_data['dietary_preference']
        )

    return render(request, 'tracker/calculator.html', {
        'initial_data': initial_data,
        'result': result,
    })


def food_database_view(request):
    """Search and browse verified USDA FoodData Central items with macro filters."""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    tag = request.GET.get('tag', '').strip()
    sort_by = request.GET.get('sort', 'protein')

    foods = FoodItem.objects.all()

    if query:
        foods = foods.filter(name__icontains=query)
    if category:
        foods = foods.filter(category=category)
    if tag:
        foods = foods.filter(dietary_tags__icontains=tag)

    if sort_by == 'protein':
        foods = foods.order_by('-protein_per_100g')
    elif sort_by == 'calories_low':
        foods = foods.order_by('calories_per_100g')
    elif sort_by == 'calories_high':
        foods = foods.order_by('-calories_per_100g')
    else:
        foods = foods.order_by('name')

    categories = FoodItem.CATEGORY_CHOICES

    return render(request, 'tracker/food_database.html', {
        'foods': foods,
        'query': query,
        'selected_category': category,
        'selected_tag': tag,
        'selected_sort': sort_by,
        'categories': categories,
    })


@login_required
def add_meal_log_view(request):
    """Add a meal log entry directly from dashboard or modal."""
    if request.method == 'POST':
        food_id = request.POST.get('food_id')
        meal_type = request.POST.get('meal_type', 'lunch')
        serving_g = float(request.POST.get('serving_g', 100))
        date_str = request.POST.get('logged_date')

        if date_str:
            try:
                logged_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                logged_date = datetime.date.today()
        else:
            logged_date = datetime.date.today()

        if food_id:
            food = get_object_or_404(FoodItem, id=food_id)
            factor = serving_g / 100.0
            MealLog.objects.create(
                user=request.user,
                food_item=food,
                food_name=food.name,
                meal_type=meal_type,
                serving_amount_g=Decimal(str(serving_g)),
                calories=Decimal(str(round(float(food.calories_per_100g) * factor, 1))),
                protein_g=Decimal(str(round(float(food.protein_per_100g) * factor, 1))),
                carbs_g=Decimal(str(round(float(food.carbs_per_100g) * factor, 1))),
                fat_g=Decimal(str(round(float(food.fat_per_100g) * factor, 1))),
                logged_date=logged_date
            )
            messages.success(request, f"Logged {serving_g}g of {food.name} to {meal_type.title()}!")
        else:
            # Custom manual entry
            food_name = request.POST.get('food_name', 'Custom Item')
            calories = float(request.POST.get('calories', 0))
            protein = float(request.POST.get('protein_g', 0))
            carbs = float(request.POST.get('carbs_g', 0))
            fat = float(request.POST.get('fat_g', 0))

            MealLog.objects.create(
                user=request.user,
                food_name=food_name,
                meal_type=meal_type,
                serving_amount_g=Decimal(str(serving_g)),
                calories=Decimal(str(calories)),
                protein_g=Decimal(str(protein)),
                carbs_g=Decimal(str(carbs)),
                fat_g=Decimal(str(fat)),
                logged_date=logged_date
            )
            messages.success(request, f"Logged {food_name} to {meal_type.title()}!")

        return redirect(f"/dashboard/?date={logged_date.isoformat()}")

    return redirect('dashboard')


@login_required
def delete_meal_log_view(request, log_id):
    """Delete a logged meal entry."""
    log = get_object_or_404(MealLog, id=log_id, user=request.user)
    date_str = log.logged_date.isoformat()
    log_name = log.food_name
    log.delete()
    messages.info(request, f"Removed {log_name} from your food log.")
    return redirect(f"/dashboard/?date={date_str}")


def ai_parse_quick_entry_api(request):
    """API endpoint to parse natural language text into food log object."""
    query = request.GET.get('query', '')
    parsed = parse_natural_language_food_entry(query)
    if parsed:
        return JsonResponse({'success': True, 'data': parsed})
    return JsonResponse({'success': False, 'message': 'No food match found. Try specifying grams (e.g. 150g chicken breast).'})


@login_required
def profile_view(request):
    """View and update profile information and recalculate targets."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            p = form.save(commit=False)
            targets = p.calculate_targets()
            p.target_calories = targets['calories']
            p.target_protein_g = targets['protein_g']
            p.target_carbs_g = targets['carbs_g']
            p.target_fat_g = targets['fat_g']
            p.save()
            messages.success(request, "Your profile and nutrition targets have been updated!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'tracker/profile.html', {
        'form': form,
        'profile': profile,
    })


# ==============================================================================
# SCIENTIFIC & TECHNICAL BIBLIOGRAPHY (Preserved in Codebase)
# The 8 authoritative references and technical frameworks underpinning the system
# ==============================================================================
SCIENTIFIC_BIBLIOGRAPHY = [
    {
        'number': 1,
        'title': 'Python Official Documentation',
        'url': 'https://www.python.org/',
        'category': 'Programming Language & Runtime',
        'role': 'Powers the core application logic, numeric decimal precision calculations, text parsing, and data modeling.',
        'highlight': 'Used Python 3.9+ object-oriented models, decimal arithmetic for exact macro tracking, and regular expression engines for natural language food entry.'
    },
    {
        'number': 2,
        'title': 'Django Documentation',
        'url': 'https://docs.djangoproject.com/',
        'category': 'Web Framework',
        'role': 'Provides the robust MVC/MVT architecture, secure user authentication, ORM database abstraction, migrations, and template rendering.',
        'highlight': 'Built using Django 4.2 LTS with integrated CSRF defense, database signals for auto-profile creation, and clean template inheritance.'
    },
    {
        'number': 3,
        'title': 'HTML Documentation',
        'url': 'https://developer.mozilla.org/en-US/docs/Web/HTML',
        'category': 'Semantic Web Standards',
        'role': 'Defines the modern semantic layout, native HTML5 dialogs, accessible forms, datalists, and ARIA attributes.',
        'highlight': 'Implemented modern semantic tags (<main>, <dialog>, <article>, <section>) ensuring high accessibility and search engine compliance.'
    },
    {
        'number': 4,
        'title': 'CSS Documentation',
        'url': 'https://developer.mozilla.org/en-US/docs/Web/CSS',
        'category': 'Responsive UI Styling',
        'role': 'Provides modern styling via CSS Custom Properties (variables), Flexbox, CSS Grid layouts, and glassmorphic card elements.',
        'highlight': 'Custom responsive design system with fluid typography, progress gauges, and mobile-friendly touch targets.'
    },
    {
        'number': 5,
        'title': 'SQLite Documentation',
        'url': 'https://www.sqlite.org/docs.html',
        'category': 'Relational Database',
        'role': 'Acts as the embedded transactional database engine storing food nutrients, user health profiles, and daily meal journals.',
        'highlight': 'Self-contained, serverless zero-configuration SQL database with ACID transaction support for instantaneous local queries.'
    },
    {
        'number': 6,
        'title': 'World Health Organization – Healthy Diet',
        'url': 'https://www.who.int/news-room/fact-sheets/detail/healthy-diet',
        'category': 'Global Health Authority',
        'role': 'Guides the macronutrient distribution ranges (AMDR) and dietary health parameters.',
        'highlight': 'System enforces WHO guidelines: total fats restricted to 20–30% of energy intake, saturated fat limits (<10%), complex carbohydrates AMDR (45–65%), and micronutrient-rich dietary patterns.'
    },
    {
        'number': 7,
        'title': 'USDA FoodData Central',
        'url': 'https://fdc.nal.usda.gov/',
        'category': 'Nutritional Database Standard',
        'role': 'Supplies verified nutritional data per 100g serving sizes across whole foods, meats, seafood, legumes, and dairy.',
        'highlight': '30+ laboratory-tested Foundation Foods pre-seeded with FoodData Central (FDC) IDs, providing exact macro breakdown, fiber, and biological protein quality.'
    },
    {
        'number': 8,
        'title': 'National Institutes of Health – Protein Guidelines',
        'url': 'https://ods.od.nih.gov/factsheets/Protein-Consumer/',
        'category': 'Clinical Nutrition & DRI Standards',
        'role': 'Establishes Recommended Dietary Allowances (RDA) and goal-based protein requirements.',
        'highlight': 'Integrates NIH dietary reference intakes: baseline 0.8g/kg for sedentary adults, scaled up to 1.6–2.2g/kg for hypertrophy and muscle retention during fat loss, plus optimal protein pacing (25–40g/meal) for Muscle Protein Synthesis (MPS).'
    },
]

def bibliography_view(request):
    """Internal code reference endpoint for scientific bibliography."""
    return render(request, 'tracker/bibliography.html', {'references': SCIENTIFIC_BIBLIOGRAPHY})


def demo_login_view(request):
    """Instant login for demonstration purposes without registration."""
    user = User.objects.filter(username='demo').first()
    if not user:
        user = User.objects.create_user(username='demo', email='demo@example.com', password='demo1234')
        user.first_name = 'Alex'
        user.last_name = 'Morgan'
        user.save()
    login(request, user)
    messages.success(request, f"Welcome back, {user.first_name or user.username}! You are logged in with demo profile data.")
    return redirect('dashboard')


def register_view(request):
    """New user sign-up with personalized baseline profile configuration."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Configure profile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.weight_kg = form.cleaned_data['weight_kg']
            profile.height_cm = form.cleaned_data['height_cm']
            profile.age = form.cleaned_data['age']
            profile.gender = form.cleaned_data['gender']
            profile.activity_level = form.cleaned_data['activity_level']
            profile.fitness_goal = form.cleaned_data['fitness_goal']
            profile.dietary_preference = form.cleaned_data['dietary_preference']

            targets = profile.calculate_targets()
            profile.target_calories = targets['calories']
            profile.target_protein_g = targets['protein_g']
            profile.target_carbs_g = targets['carbs_g']
            profile.target_fat_g = targets['fat_g']
            profile.save()

            login(request, user)
            messages.success(request, f"Welcome to AI Protein Tracker, {user.username}! Your nutrition plan is ready.")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'tracker/register.html', {'form': form})


def login_view(request):
    """User authentication view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'tracker/login.html', {'form': form})


def logout_view(request):
    """User sign-out view."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')
