# chatbot_auth/views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import SignupForm, SigninForm
from social_django.utils import psa
from social_core.exceptions import AuthCanceled, AuthAlreadyAssociated


def check_authentication(request):
    return JsonResponse({"is_authenticated": request.user.is_authenticated})


def signup_signin_view(request):
    signup_form = SignupForm()
    signin_form = SigninForm()
    return render(request, 'chatbot_auth/signup_signin.html', {
        'signup_form': signup_form,
        'signin_form': signin_form
    })


def auth_view(request):
    signup_form = SignupForm()
    signin_form = SigninForm(request, data=request.POST) if request.method == 'POST' else SigninForm()

    if request.method == 'POST':
        if 'signup_submit' in request.POST:
            signup_form = SignupForm(request.POST)
            if signup_form.is_valid():
                user = signup_form.save()
                messages.success(request, 'Account created successfully! Please sign in.')
                return redirect('chatbot_auth:signup_signin')
            else:
                # Pass form errors to the template instead of just a generic message
                pass  # Errors are already in signup_form.errors

        elif 'signin_submit' in request.POST:
            signin_form = SigninForm(request, data=request.POST)
            if signin_form.is_valid():
                user = signin_form.get_user()
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('admin_panel:dashboard')

    return render(request, 'chatbot_auth/signup_signin.html', {
        'signup_form': signup_form,
        'signin_form': signin_form
    })


@psa('social:complete')
def social_auth_complete(request, backend):
    try:
        user = request.backend.strategy.authenticate(request, backend=backend)
        if user:
            messages.success(request, f"Account linked with {backend.capitalize()}! Please sign in.")
            return redirect('chatbot_auth:signup_signin')
        else:
            messages.error(request, "Social login failed.")
            return redirect('chatbot_auth:signup_signin')
    except AuthCanceled:
        messages.info(request, "Authentication canceled.")
        return redirect('chatbot_auth:signup_signin')
    except AuthAlreadyAssociated:
        messages.error(request, "This account is already associated.")
        return redirect('chatbot_auth:signup_signin')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('chatbot_auth:signup_signin')


@login_required
def dashboard_view(request):
    if not request.user.is_staff:
        messages.warning(request, "Access denied: Admins only.")
        return redirect('home')
    return render(request, 'admin_panel/dashboard.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('chatbot_auth:signup_signin')
