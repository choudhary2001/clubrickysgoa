from django.urls import path
from django.http import Http404
from . import views

def test_404(request):
    raise Http404("Test 404 page")

urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.home, name='index'),
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('events/', views.events, name='events'),
    path('menu/', views.menu, name='menu'),
    path('contact/', views.contact, name='contact'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('refund/', views.refund, name='refund'),
    path('events/<int:event_id>/book/', views.book_event, name='book_event'),
    path('events/<int:event_id>/process-booking/', views.process_booking, name='process_booking'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
    path('gallery/', views.gallery, name='gallery'),
    path('download-ticket/<int:booking_id>/', views.download_ticket, name='download_ticket'),
    path('test-404/', views.test_404_view, name='test_404'),
    path('food-menu/', views.food_menu, name='food_menu'),
    path('bar-menu/', views.bar_menu, name='bar_menu'),
] 