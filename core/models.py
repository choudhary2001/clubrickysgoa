from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    terms_and_conditions = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    
    # Pricing
    stag_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    couple_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Capacity
    total_seats = models.PositiveIntegerField()
    available_seats = models.PositiveIntegerField()
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Add image field for event banner/poster
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # If this is a new event, set available seats equal to total seats
        if not self.pk:
            self.available_seats = self.total_seats
        super().save(*args, **kwargs)

class EventBooking(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_bookings')
    
    TICKET_TYPE_CHOICES = [
        ('STAG', 'Stag'),
        ('COUPLE', 'Couple'),
    ]
    
    ticket_type = models.CharField(
        max_length=10,
        choices=TICKET_TYPE_CHOICES
    )
    seat_count = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment details
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    payment_id = models.CharField(max_length=100, blank=True)
    payment_response = models.JSONField(null=True, blank=True)
    
    # Booking status
    is_confirmed = models.BooleanField(default=False)
    booking_reference = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    stag_count = models.PositiveIntegerField(default=0)
    couple_count = models.PositiveIntegerField(default=0)

    phone_number = models.CharField(max_length=15, blank=True)


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.event.title}"

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = (self.stag_count * self.event.stag_fee) + (self.couple_count * self.event.couple_fee)
        
        # Generate booking reference if not exists
        if not self.booking_reference:
            import uuid
            self.booking_reference = str(uuid.uuid4()).split('-')[0].upper()
        
        super().save(*args, **kwargs)

    def confirm_booking(self):
        """Confirm the booking and update event availability"""
        if not self.is_confirmed and self.payment_status == 'COMPLETED':
            # Check if enough seats are available
            if self.event.available_seats >= self.seat_count:
                self.event.available_seats -= self.seat_count
                self.event.save()
                
                self.is_confirmed = True
                self.save()
                return True
        return False

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Easebuzz', 'Easebuzz'),
        # Add other payment methods as needed
    ]

    booking = models.OneToOneField(EventBooking, on_delete=models.CASCADE, related_name='payment_details')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_status = models.CharField(max_length=20)
    payment_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.booking.booking_reference}"

class MenuCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Menu Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('OUT_OF_STOCK', 'Out of Stock'),
        ('COMING_SOON', 'Coming Soon'),
    ]

    category = models.ForeignKey(
        MenuCategory, 
        on_delete=models.CASCADE,
        related_name='items'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        upload_to='menu_items/',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='AVAILABLE'
    )
    is_vegetarian = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order', 'title']

    def __str__(self):
        return f"{self.title} - {self.category.name}"

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

class GalleryImageCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Gallery Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def image_count(self):
        return self.galleryimage_set.count()

class GalleryImage(models.Model):
    category = models.ForeignKey(
        GalleryImageCategory, 
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    title = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to='gallery_images/')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or f"Image {self.id}"

class TeamCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Team Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
        
    def member_count(self):
        return self.members.count()

class TeamMember(models.Model):
    category = models.ForeignKey(
        TeamCategory, 
        on_delete=models.CASCADE,
        related_name='members'
    )
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = models.TextField()
    image = models.ImageField(upload_to='team_members/')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order', 'name']

    def __str__(self):
        return f"{self.name} - {self.position}"

class JobApplication(models.Model):
    POSITION_CHOICES = [
        ('bartender', 'Bartender'),
        ('server', 'Server'),
        ('chef', 'Chef'),
        ('kitchen-staff', 'Kitchen Staff'),
        ('dj', 'DJ'),
        ('security', 'Security'),
        ('management', 'Management'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('under_review', 'Under Review'),
        ('interview', 'Interview Scheduled'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ]
    
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)
    experience = models.TextField()
    message = models.TextField()
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.full_name} - {self.get_position_display()}"
