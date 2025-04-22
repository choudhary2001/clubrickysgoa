from django.shortcuts import render, redirect, get_object_or_404
from .models import MenuCategory, Contact, Event, EventBooking, GalleryImage, GalleryImageCategory, TeamCategory, TeamMember, JobApplication
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from .easebuzz_lib.easebuzz_payment_gateway import Easebuzz
import uuid
import json
from django.urls import reverse
import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.template.loader import render_to_string
import pdfkit
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import Http404

def index(request):
    return render(request, 'index.html') 

def home(request):
    # Get upcoming events
    upcoming_events = Event.objects.filter(
        date__gte=timezone.now().date(),
        is_active=True
    ).order_by('date')[:3]
    
    # Get gallery images for preview
    gallery_images = GalleryImage.objects.all()[:8]
    
    return render(request, 'core/home.html', {
        'upcoming_events': upcoming_events,
        'gallery_images': gallery_images,
    })

def about(request):
    # Handle job application form submission
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full-name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            position = request.POST.get('position')
            experience = request.POST.get('experience')
            message = request.POST.get('message')
            resume = request.FILES.get('resume')
            
            # Create job application
            JobApplication.objects.create(
                full_name=full_name,
                email=email,
                phone=phone,
                position=position,
                experience=experience,
                message=message,
                resume=resume
            )
            
            messages.success(request, 'Your application has been submitted successfully! We will review it and contact you soon.')
            return redirect('about')
        except Exception as e:
            messages.error(request, f'There was an error submitting your application. Please try again. Error: {str(e)}')
            return redirect('about')
    
    team_categories = TeamCategory.objects.filter(is_active=True).prefetch_related(
        'members'
    ).order_by('order', 'name')
    print(team_categories)

    return render(request, 'core/about.html', {
        'team_categories': team_categories,
    })

def events(request):
    # Get all active events that haven't ended yet
    events = Event.objects.filter(
        is_active=True,
        date__gte=timezone.now().date()
    ).order_by('date', 'start_time')
    
    return render(request, 'core/events.html', {
        'events': events
    }) 

def menu(request):
    categories = MenuCategory.objects.prefetch_related('items').all()
    return render(request, 'core/menu.html', {
        'categories': categories
    }) 

def contact(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            message = request.POST.get('message')
            
            Contact.objects.create(
                name=name,
                email=email,
                message=message
            )
            messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
            return redirect('contact')
        except Exception as e:
            messages.error(request, 'There was an error sending your message. Please try again.')
            return redirect('contact')
    
    return render(request, 'core/contact.html')

def terms(request):
    return render(request, 'core/terms.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def refund(request):
    return render(request, 'core/refund.html')

def book_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    max_couple_tickets = event.available_seats // 2  # Calculate max couple tickets
    
    if not event.is_active or event.available_seats <= 0:
        messages.error(request, 'Sorry, this event is no longer available for booking.')
        return redirect('events')
    
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to book an event.')
        return redirect('login')
    
    return render(request, 'core/event_booking.html', {
        'event': event,
        'max_couple_tickets': max_couple_tickets
    })

def process_booking(request, event_id):
    if request.method == 'POST':
        event = get_object_or_404(Event, id=event_id)
        stag_count = int(request.POST.get('stag_count', 0))
        couple_count = int(request.POST.get('couple_count', 0))
        phone = request.POST.get('phone', '').strip()
        
        if stag_count == 0 and couple_count == 0:
            messages.error(request, 'Please select at least one ticket.')
            return redirect('book_event', event_id=event_id)
        
        # Calculate actual seats needed
        seats_needed = stag_count + (couple_count * 2)
        if seats_needed > event.available_seats:
            messages.error(request, 'Sorry, not enough seats available.')
            return redirect('book_event', event_id=event_id)
        
        # Calculate total amount
        total_amount = (stag_count * event.stag_fee) + (couple_count * event.couple_fee)
        
        # Create booking
        booking = EventBooking.objects.create(
            event=event,
            user=request.user,
            stag_count=stag_count,
            couple_count=couple_count,
            total_amount=total_amount,
            booking_reference=f"BOOK-{uuid.uuid4().hex[:8].upper()}",
            payment_status='PENDING',
            phone_number=phone
        )
        
        # Create or update user profile with phone
        if hasattr(request.user, 'profile'):
            request.user.profile.phone = phone
            request.user.profile.save()
        
        # Initialize Easebuzz payment
        easebuzz = Easebuzz(
            merchant_key="EFTU4F7D2P",
            salt="VLJEMDDX7X",
            env="prod"
        )
        
        # Prepare payment data
        post_data = {
            'key': easebuzz.merchant_key,
            'txnid': booking.booking_reference,
            'amount': str(booking.total_amount),
            'firstname': booking.user.first_name or booking.user.username,
            'email': booking.user.email,
            'phone': phone,
            'productinfo': f"Event Booking - {booking.event.title}",
            'surl': request.build_absolute_uri(reverse('payment_success')),
            'furl': request.build_absolute_uri(reverse('payment_failure')),
            'udf1': str(booking.id),
            'udf2': '',
            'udf3': '',
            'udf4': '',
            'udf5': '',
            'hash': ''  # Will be generated below
        }
        
        # Generate hash string
        hash_string = (
            f"{easebuzz.merchant_key}|{post_data['txnid']}|{post_data['amount']}|{post_data['productinfo']}|"
            f"{post_data['firstname']}|{post_data['email']}|{post_data['udf1']}|{post_data['udf2']}|{post_data['udf3']}|"
            f"{post_data['udf4']}|{post_data['udf5']}||||||{easebuzz.salt}"
        )
        
        # Generate hash
        post_data['hash'] = hashlib.sha512(hash_string.encode()).hexdigest()
        
        return render(request, 'core/payment_redirect.html', {
            'booking': booking,
            'payment_url': 'https://pay.easebuzz.in/pay/secure',
            'payment_data': post_data
        })
            
    return redirect('book_event', event_id=event_id)

@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        easebuzz = Easebuzz(
            merchant_key="EFTU4F7D2P",
            salt="VLJEMDDX7X",
            env="prod"
        )
        print(request.POST)
        print(easebuzz)
        # Verify response hash
        hash_string = (
            f"{easebuzz.merchant_key}|{request.POST.get('txnid')}|"
            f"{request.POST.get('amount')}|{request.POST.get('productinfo')}|{request.POST.get('firstname')}|"
            f"{request.POST.get('email')}|{request.POST.get('phone')}|{request.POST.get('udf1')}|"
            f"{request.POST.get('udf2')}|{request.POST.get('udf3')}|{request.POST.get('udf4')}|"
            f"{request.POST.get('udf5')}||||||{easebuzz.salt}"
        )
        print(hash_string)
        generated_hash = hashlib.sha512(hash_string.encode()).hexdigest()
        received_hash = request.POST.get('hash')
        print(generated_hash)
        # if generated_hash == received_hash:
        booking_id = request.POST.get('udf1')
        booking = get_object_or_404(EventBooking, id=booking_id)
        print(booking)
        if booking.payment_status != 'COMPLETED':
            booking.payment_status = 'COMPLETED'
            booking.payment_id = request.POST.get('txnid')
            booking.payment_response = request.POST.dict()
            booking.is_confirmed = True
            booking.save()

            payment = Payment.objects.create(
                booking=booking,
                payment_method='Easebuzz',
                amount=booking.total_amount,
                transaction_id=request.POST.get('txnid'),
                payment_status='COMPLETED',
                payment_response=request.POST.dict()
            )
            payment.save()
            # Update event available seats
            event = booking.event
            event.available_seats -= booking.stag_count
            event.available_seats -= 2 *booking.couple_count
            event.save()
            print(event)
        return render(request, 'core/payment_success.html', {
            'booking': booking
        })
    
    messages.error(request, 'Invalid payment verification.')
    return redirect('events')

@csrf_exempt
def payment_failure(request):
    if request.method == 'POST':
        txnid = request.POST.get('txnid')
        if txnid:
            try:
                booking = EventBooking.objects.get(booking_reference=txnid)
                if booking.payment_status != 'FAILED':
                    booking.payment_status = 'FAILED'
                    booking.payment_response = request.POST.dict()
                    booking.save()
                
                return render(request, 'core/payment_failure.html', {
                    'booking': booking
                })
            except EventBooking.DoesNotExist:
                pass
    
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('events')

def gallery(request):
    categories = GalleryImageCategory.objects.filter(is_active=True)
    selected_category = request.GET.get('category')
    
    context = {
        'categories': categories,
        'selected_category': int(selected_category) if selected_category and selected_category.isdigit() else None
    }
    return render(request, 'core/gallery.html', context)

@login_required
def download_ticket(request, booking_id):
    booking = get_object_or_404(EventBooking, id=booking_id, user=request.user)
    
    if booking.payment_status != 'COMPLETED':
        messages.error(request, 'This booking is not confirmed.')
        return redirect('profile')
    
    # Render the ticket template to HTML
    html = render_to_string('core/ticket.html', {
        'booking': booking,
        'request': request,
    })
    
    # Convert HTML to PDF
    options = {
        'page-size': 'A4',
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
    }
    
    pdf = pdfkit.from_string(html, False, options=options)
    
    # Create the HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{booking.booking_reference}.pdf"'
    
    return response

def test_404_view(request):
    # Force a 404 response even when DEBUG is True
    return render(request, '404.html', status=404)


def food_menu(request):
    return render(request, 'core/food_menu.html')

def bar_menu(request):
    return render(request, 'core/bar_menu.html')

