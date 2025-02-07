from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, SigninForm


def auth_view(request):
    signup_form = SignupForm()
    signin_form = SigninForm()

    if request.method == 'POST':
        if 'signup_submit' in request.POST:
            signup_form = SignupForm(request.POST)
            if signup_form.is_valid():
                user = signup_form.save(commit=False)
                user.set_password(signup_form.cleaned_data['password'])
                user.save()
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('chatbot_auth:auth')
            else:
                messages.error(request, 'Please correct the errors below.')

        elif 'signin_submit' in request.POST:
            signin_form = SigninForm(request, data=request.POST)
            if signin_form.is_valid():
                username = signin_form.cleaned_data.get('username')
                password = signin_form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Login successful!')
                    return redirect('chatbot_home')
                else:
                    messages.error(request, 'Invalid username or password.')

    return render(request, 'chatbot_auth/signup_signin.html', {
        'signup_form': signup_form,
        'signin_form': signin_form
    })


@login_required
def signout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('chatbot_auth:auth')