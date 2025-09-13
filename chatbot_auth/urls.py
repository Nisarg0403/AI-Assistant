from django.urls import path
from . import views

app_name = "chatbot_auth"

urlpatterns = [
    path("signup-signin/", views.signup_signin_view, name="signup_signin"),
    path("auth/", views.auth_view, name="auth"),
    path("logout/", views.logout_view, name="logout"),
    path("check-auth/", views.check_authentication, name="check_auth"),
    path("forgot/", views.forgot, name="forgot"),
    path("reset/<uidb64>/<token>/", views.reset, name="reset"),
]