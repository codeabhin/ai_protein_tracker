from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, FoodItem, MealLog

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input', 'placeholder': 'Create a secure password'
    }))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input', 'placeholder': 'Confirm your password'
    }))

    # Initial profile questions
    weight_kg = forms.DecimalField(initial=70.0, widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}))
    height_cm = forms.DecimalField(initial=175.0, widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}))
    age = forms.IntegerField(initial=25, widget=forms.NumberInput(attrs={'class': 'form-input'}))
    gender = forms.ChoiceField(choices=UserProfile.GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    activity_level = forms.ChoiceField(choices=UserProfile.ACTIVITY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    fitness_goal = forms.ChoiceField(choices=UserProfile.GOAL_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    dietary_preference = forms.ChoiceField(choices=UserProfile.DIET_PREFERENCES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email address'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['weight_kg', 'height_cm', 'age', 'gender', 'activity_level', 'fitness_goal', 'dietary_preference']
        widgets = {
            'weight_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'height_cm': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'age': forms.NumberInput(attrs={'class': 'form-input'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
            'fitness_goal': forms.Select(attrs={'class': 'form-select'}),
            'dietary_preference': forms.Select(attrs={'class': 'form-select'}),
        }


class MealLogForm(forms.ModelForm):
    class Meta:
        model = MealLog
        fields = ['food_item', 'food_name', 'meal_type', 'serving_amount_g', 'calories', 'protein_g', 'carbs_g', 'fat_g']
        widgets = {
            'food_item': forms.HiddenInput(),
            'food_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Food name or select below'}),
            'meal_type': forms.Select(attrs={'class': 'form-select'}),
            'serving_amount_g': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'step': '1'}),
            'calories': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'protein_g': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'carbs_g': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'fat_g': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
        }


class CustomFoodForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ['name', 'category', 'calories_per_100g', 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g', 'fiber_per_100g', 'serving_size_g', 'serving_unit_name', 'dietary_tags']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Greek Feta Salad'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'calories_per_100g': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'kcal / 100g'}),
            'protein_per_100g': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'g / 100g'}),
            'carbs_per_100g': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'g / 100g'}),
            'fat_per_100g': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'g / 100g'}),
            'fiber_per_100g': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'g / 100g'}),
            'serving_size_g': forms.NumberInput(attrs={'class': 'form-input', 'step': '1', 'placeholder': 'e.g. 150'}),
            'serving_unit_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 1 bowl (150g)'}),
            'dietary_tags': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. vegetarian, gluten-free'}),
        }
