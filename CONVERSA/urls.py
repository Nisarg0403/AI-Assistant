# CONVERSA/urls.py
from django.contrib import admin
from django.urls import path, include
from admin_panel.views import dashboard_view
from chatbot_project.views import homepage
from chatbot_auth import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", homepage, name="home"),
    path("chatbot/", include("chatbot_project.urls")),
    path('chatbot-auth/', include('chatbot_auth.urls')),
    path("admin_panel/", include("admin_panel.urls")),
    path("auth/", include("social_django.urls", namespace="social")),  # Correct for social auth

# Temporary explicit path
    path('chatbot_auth/reset/<uidb64>/<token>/', views.reset, name='reset'),
]