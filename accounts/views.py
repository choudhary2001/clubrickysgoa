from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import uuid
from .forms import CustomUserCreationForm, UserProfileForm, OTPVerificationForm
from .models import CustomUser
from core.models import EventBooking

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.verification_token = str(uuid.uuid4())
            user.save()

            # Send verification email
            verification_link = request.build_absolute_uri(
                reverse('verify_email', args=[user.verification_token])
            )
            
            # Create HTML email
            context = {
                'user': user,
                'verification_link': verification_link,
            }
            html_content = render_to_string('emails/verification_email.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                "Verify your email - Club Ricky's Goa",
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            login(request, user)
            messages.success(request, 'Registration successful! Please verify your email.')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def verify_email(request, token):
    try:
        user = CustomUser.objects.get(verification_token=token)
        user.email_verified = True
        user.verification_token = ''
        user.save()
        messages.success(request, 'Email verified successfully!')
        return render(request, 'registration/verification_success.html')
    except CustomUser.DoesNotExist:
        return render(request, 'registration/verification_failed.html')

@login_required
def profile(request):
    # Get user's bookings ordered by date
    bookings = EventBooking.objects.filter(user=request.user).order_by('-created_at')
    print('bookings', bookings)
    return render(request, 'accounts/profile.html', {
        'bookings': bookings
    })



@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Generate and send OTP
            otp = user.generate_otp()
            
            # Send OTP email
            context = {
                'user': user,
                'otp': otp,
            }
            html_content = render_to_string('emails/otp_email.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                "Login OTP - Club Ricky's Goa",
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            # Store user ID in session for OTP verification
            request.session['login_user_id'] = user.id
            return redirect('verify_otp')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')

def verify_otp(request):
    user_id = request.session.get('login_user_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return redirect('login')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            
            # Check if OTP is expired (10 minutes validity)
            if user.otp_created_at and timezone.now() - user.otp_created_at > timedelta(minutes=10):
                messages.error(request, 'OTP has expired. Please try again.')
                return redirect('login')
            
            if user.otp == otp:
                login(request, user)
                user.otp = ''  # Clear OTP after successful verification
                user.save()
                del request.session['login_user_id']
                messages.success(request, 'Login successful!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'registration/verify_otp.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home') 