from django.urls import path
from .views import auth_view, signout_view

app_name = 'chatbot_auth'

urlpatterns = [
    path('auth/', auth_view, name='auth'),
    path('signout/', signout_view, name='signout'),
]