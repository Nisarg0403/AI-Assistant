from django.urls import path
from . import views

app_name = "chatbot_auth"

urlpatterns = [
    path("signup-signin/", views.signup_signin_view, name="signup_signin"),
    path("auth/", views.auth_view, name="auth"),  # Changed to 'auth'
    path("logout/", views.logout_view, name="logout"),
    path("check-auth/", views.check_authentication, name="check_auth"),
    # Remove: path("auth/complete/google-oauth2/", views.social_auth_complete, name="social_complete_google"),
]