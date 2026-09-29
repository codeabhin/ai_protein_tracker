from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('calculator/', views.calculator_view, name='calculator'),
    path('foods/', views.food_database_view, name='food_database'),
    path('profile/', views.profile_view, name='profile'),

    # Actions & APIs
    path('meals/add/', views.add_meal_log_view, name='add_meal_log'),
    path('meals/delete/<int:log_id>/', views.delete_meal_log_view, name='delete_meal_log'),
    path('api/parse-food/', views.ai_parse_quick_entry_api, name='api_parse_food'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('demo-login/', views.demo_login_view, name='demo_login'),
]
