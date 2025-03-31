# chatbot_auth/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
import random


class SignupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'Create password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Choose username'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Enter your name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input-field',
                'placeholder': 'Enter email'
            })
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            # Suggest a unique username by appending a random number
            suggestion = f"{username}{random.randint(1, 999)}"
            raise forms.ValidationError(
                f"The username '{username}' is already taken. How about '{suggestion}'?"
            )
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class SigninForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Enter username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'Enter password'
        })
    )
