from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'chatbot_project'
urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('chatbot/chat/', views.chatbot_view, name='chatbot_home'),
    path('pricing/', TemplateView.as_view(template_name="chatbot/pricing.html"), name='pricing'),
    path('get_response/', views.get_response, name='chatbot_response'),
    path('get_sub_faqs/<int:faq_id>/', views.get_sub_faqs, name='get_sub_faqs'),
    path('check-authentication/', views.check_authentication, name='check_ cauthentication'),
    path('get_faqs/', views.get_faqs, name='get_faqs'),  # Fixed path
]