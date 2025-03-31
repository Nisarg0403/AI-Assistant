from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('manage-faqs/', views.manage_faqs, name='manage_faqs'),
    path('edit_faq/<int:faq_id>/', views.edit_faq, name='edit_faq'),
    path('delete-faq/<int:faq_id>/', views.delete_faq, name='delete_faq'),
]