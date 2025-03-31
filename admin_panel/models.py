# admin_panel/models.py
from django.db import models
from django.utils import timezone


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField(blank=True, null=True)  # Made nullable for parent FAQs
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


class ChatbotTheme(models.Model):
    theme_name = models.CharField(max_length=100, unique=True)
    primary_background_color = models.CharField(max_length=7, default='#1a1a1a')
    secondary_background_color = models.CharField(max_length=7, default='#2d2d2d')
    nav_background_color = models.CharField(max_length=7, default='#2d2d2d')
    text_color = models.CharField(max_length=7, default='#ffffff')
    accent_color = models.CharField(max_length=7, default='#7289da')
    user_message_color = models.CharField(max_length=7, default='#4CAF50')
    bot_message_color = models.CharField(max_length=7, default='#7289da')
    bot_icon_background_color = models.CharField(max_length=7, default='#ff9800')
    gradient_start_color = models.CharField(max_length=7, default='#7289da')
    gradient_end_color = models.CharField(max_length=7, default='#a8b8ff')
    font_family = models.CharField(max_length=100, default='Inter, sans-serif')
    navbar_text_color = models.CharField(max_length=7, default='#ffffff')
    button_padding = models.CharField(max_length=50, default='12px 24px')
    button_border_radius = models.CharField(max_length=50, default='10px')
    button_font_size = models.CharField(max_length=50, default='16px')
    message_animation_duration = models.FloatField(default=0.3)
    message_icon_size = models.IntegerField(default=35)
    suggestion_button_padding = models.CharField(max_length=50, default='10px 20px')
    suggestion_button_border_radius = models.CharField(max_length=50, default='50px')

    def __str__(self):
        return self.theme_name


class QueryLog(models.Model):
    query_text = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    matched_faq = models.ForeignKey(FAQ, on_delete=models.SET_NULL, null=True, blank=True)
    unresolved = models.BooleanField(default=False)
    response_time = models.FloatField(default=0)  # Added for avg response time metric
    is_lead = models.BooleanField(default=False)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # Add this

    def __str__(self):
        return f"{self.query_text} ({self.timestamp})"
