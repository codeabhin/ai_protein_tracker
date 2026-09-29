from django.contrib import admin
from .models import UserProfile, FoodItem, MealLog

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'fitness_goal', 'activity_level', 'target_protein_g', 'target_calories', 'updated_at')
    list_filter = ('fitness_goal', 'activity_level', 'gender', 'dietary_preference')
    search_fields = ('user__username', 'user__email')

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'protein_per_100g', 'calories_per_100g', 'is_verified', 'usda_fdc_id')
    list_filter = ('category', 'is_verified')
    search_fields = ('name', 'usda_fdc_id', 'dietary_tags')

@admin.register(MealLog)
class MealLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'food_name', 'meal_type', 'serving_amount_g', 'protein_g', 'calories', 'logged_date')
    list_filter = ('meal_type', 'logged_date')
    search_fields = ('user__username', 'food_name')
