from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
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
               pass

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


# chatbot_auth/views.py
def forgot(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        print(f"Received email: {email}")
        try:
            # Use filter() and take the first user if multiple exist
            users = User.objects.filter(email=email)
            if users.exists():
                user = users.first()  # Take the first user
                print(f"Found user: {user.username}")
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_link = request.build_absolute_uri(f"/chatbot_auth/reset/{uid}/{token}/")
                print(f"Reset link: {reset_link}")
                subject = "Reset Your CONVERSA Password"
                html_message = render_to_string('chatbot_auth/reset_password_email.html', {
                    'user': user,
                    'reset_link': reset_link,
                })
                send_mail(
                    subject,
                    message='',  # Plain text message (empty since we're using HTML)
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                    html_message=html_message,  # Specify HTML content here
                )
                print("Email sent successfully")
                messages.success(request, "If an account exists with this email, a reset link has been sent.")
                return redirect('chatbot_auth:signup_signin')
            else:
                print("User not found")
                messages.success(request, "If an account exists with this email, a reset link has been sent.")
                return redirect('chatbot_auth:signup_signin')
        except Exception as e:
            print(f"Error: {e}")
            messages.error(request, "An error occurred. Please try again later.")
            return render(request, 'chatbot_auth/forgot.html')
    print("Rendering forgot page")
    return render(request, 'chatbot_auth/forgot.html')


# Updated to 'reset'
# chatbot_auth/views.py
def reset(request, uidb64, token):
    print(f"Reset view called with uidb64={uidb64}, token={token}")
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        print(f"Decoded UID: {uid}")
        user = User.objects.get(pk=uid)
        print(f"Found user: {user.username}")
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        print(f"Error decoding UID or finding user: {e}")
        user = None

    if user and default_token_generator.check_token(user, token):
        print("Token is valid")
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            if password == confirm_password:
                user.set_password(password)
                user.save()
                print("Password reset successfully")
                messages.success(request, "Password reset successfully. Please sign in.")
                return redirect('chatbot_auth:signup_signin')
            else:
                print("Passwords do not match")
                messages.error(request, "Passwords do not match.")
                return render(request, 'chatbot_auth/reset.html', {'uidb64': uidb64, 'token': token})
        return render(request, 'chatbot_auth/reset.html', {'uidb64': uidb64, 'token': token})
    else:
        print("Invalid or expired token")
        messages.error(request, "The reset link is invalid or has expired.")
        return redirect('chatbot_auth:forgot')