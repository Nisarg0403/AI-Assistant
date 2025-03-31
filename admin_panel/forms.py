# admin_panel/forms.py
from django import forms
from .models import FAQ


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'parent']
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = FAQ.objects.all()
        self.fields['parent'].label = "Parent FAQ (optional)"
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = "None"  # Adds "None" option
