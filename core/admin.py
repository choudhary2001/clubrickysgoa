from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from unfold.admin import ModelAdmin
from .models import Event, EventBooking, Payment, MenuCategory, MenuItem, Contact, GalleryImage, GalleryImageCategory, TeamCategory, TeamMember, JobApplication
from django import forms

@admin.register(Event)
class EventAdmin(ModelAdmin):
    search_fields = ('title', 'description', 'location')
    list_filter = ('is_active', 'date', 'created_at')
    list_display = ('title', 'event_date', 'event_time', 'seats_status', 'price_display', 'status_badge')
    readonly_fields = ('available_seats', 'created_at', 'updated_at')

    # Unfold specific settings
    ordering = ('-created_at',)
    
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "title",
                    "description",
                    "image",
                    "is_active",
                ],
            },
        ),
        (
            "Event Details",
            {
                "fields": [
                    ("date", "start_time", "end_time"),
                    "location",
                    "terms_and_conditions",
                ],
            },
        ),
        (
            "Pricing & Capacity",
            {
                "fields": [
                    ("stag_fee", "couple_fee"),
                    ("total_seats", "available_seats"),
                ],
            },
        ),
        (
            "System Fields",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["make_active", "make_inactive"]

    @admin.action(description="Mark selected events as active")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Mark selected events as inactive")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    def event_date(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">event</span>'
            '<span>{}</span>'
            '</div>',
            obj.date.strftime("%d %b, %Y")
        )
    event_date.short_description = "Date"

    def event_time(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">schedule</span>'
            '<span>{} - {}</span>'
            '</div>',
            obj.start_time.strftime("%I:%M %p"),
            obj.end_time.strftime("%I:%M %p")
        )
    event_time.short_description = "Time"

    def seats_status(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">event_seat</span>'
            '<span>{} / {}</span>'
            '</div>',
            obj.available_seats,
            obj.total_seats
        )
    seats_status.short_description = "Seats"

    def price_display(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">attach_money</span>'
            '<span>Stag: ₹{} | Couple: ₹{}</span>'
            '</div>',
            obj.stag_fee,
            obj.couple_fee
        )
    price_display.short_description = "Pricing"

    def status_badge(self, obj):
        status = "Active" if obj.is_active else "Inactive"
        color = "green" if obj.is_active else "red"
        return format_html(
            '<span class="flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-{}-100 text-{}-800" style="color:black;">'
            '<span class="material-icons-outlined text-base mr-1">check_circle</span>{}'
            '</span>',
            color, color, status
        )
    status_badge.short_description = "Status"

@admin.register(EventBooking)
class EventBookingAdmin(ModelAdmin):
    search_fields = ('booking_reference', 'user__email', 'user__username', 'event__title')
    list_filter = ('payment_status', 'is_confirmed', 'created_at', 'event')
    list_display = ('booking_reference', 'event_link', 'user_info', 'booking_details', 'payment_badge', 'booking_status')
    readonly_fields = ('booking_reference', 'total_amount', 'created_at', 'updated_at')
    
    # Unfold specific settings
    ordering = ('-created_at',)
    
    fieldsets = [
        (
            "Booking Information",
            {
                "fields": [
                    "booking_reference",
                    ("event", "user"),
                    ("stag_count", "couple_count"),
                    "total_amount",
                ],
            },
        ),
        (
            "Payment Information",
            {
                "fields": [
                    "payment_status",
                    "payment_id",
                    "payment_response",
                    "is_confirmed",
                ],
            },
        ),
        (
            "System Fields",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["confirm_bookings", "cancel_bookings"]

    @admin.action(description="Confirm selected bookings")
    def confirm_bookings(self, request, queryset):
        for booking in queryset:
            booking.confirm_booking()

    @admin.action(description="Cancel selected bookings")
    def cancel_bookings(self, request, queryset):
        queryset.update(is_confirmed=False)

    def event_link(self, obj):
        url = reverse('admin:core_event_change', args=[obj.event.id])
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">event</span>'
            '<a href="{}" class="text-primary-600 hover:text-primary-900">{}</a>'
            '</div>',
            url, obj.event.title
        )
    event_link.short_description = "Event"

    def user_info(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">person</span>'
            '<div>'
            '<div class="font-medium">{}</div>'
            '<div class="text-sm text-gray-500">{}</div>'
            '</div>'
            '</div>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    user_info.short_description = "User"

    def booking_details(self, obj):
        return format_html(
            '<div class="space-y-1">'
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">person</span>'
            '<span>Stag: {}</span>'
            '</div>'
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">people</span>'
            '<span>Couple: {}</span>'
            '</div>'
            '<div class="flex items-center font-medium">'
            '<span class="material-icons-outlined text-gray-400 mr-2">payments</span>'
            '<span>Total: ₹{}</span>'
            '</div>'
            '</div>',
            obj.stag_count, obj.couple_count, obj.total_amount
        )
    booking_details.short_description = "Booking Details"

    def payment_badge(self, obj):
        status_config = {
            'PENDING': ('pending', 'bg-yellow-100 text-yellow-800'),
            'COMPLETED': ('check_circle', 'bg-green-100 text-green-800'),
            'FAILED': ('cancel', 'bg-red-100 text-red-800'),
            'REFUNDED': ('replay', 'bg-blue-100 text-blue-800')
        }
        icon, badge_class = status_config.get(obj.payment_status, ('help', 'bg-gray-100 text-gray-800'))
        
        return format_html(
            '<div class="flex items-center" style="color:grey;">'
            '<span class="material-icons-outlined text-current mr-2">{}</span>'
            '<span class="px-2 py-1 text-xs font-medium rounded-full {}">{}</span>'
            '</div>',
            icon, badge_class, obj.payment_status
        )
    payment_badge.short_description = "Payment"

    def booking_status(self, obj):
        if obj.is_confirmed:
            badge_class = 'bg-green-100 text-green-800'
            status = 'Confirmed'
            icon = 'check_circle'
        else:
            badge_class = 'bg-yellow-100 text-yellow-800'
            status = 'Pending'
            icon = 'pending'
        
        return format_html(
            '<div class="flex items-center" >'
            '<span class="material-icons-outlined text-current mr-2">{}</span>'
            '<span class="px-2 py-1 text-xs font-medium rounded-full {}">{}</span>'
            '</div>',
            icon, badge_class, status
        )
    booking_status.short_description = "Status"

@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    search_fields = ('transaction_id', 'booking__booking_reference')
    list_filter = ('payment_method', 'payment_status', 'created_at')
    list_display = ('transaction_id', 'booking_link', 'payment_method', 'amount_display', 'payment_badge', 'payment_date')
    readonly_fields = ('created_at', 'updated_at')

    # Unfold specific settings
    ordering = ('-created_at',)
    
    fieldsets = [
        (
            "Payment Details",
            {
                "fields": [
                    "transaction_id",
                    ("booking", "payment_method"),
                    "amount",
                ],
            },
        ),
        (
            "Status & Response",
            {
                "fields": [
                    "payment_status",
                    "payment_response",
                ],
            },
        ),
        (
            "System Fields",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["mark_as_completed", "mark_as_failed"]

    @admin.action(description="Mark selected payments as completed")
    def mark_as_completed(self, request, queryset):
        queryset.update(payment_status='COMPLETED')

    @admin.action(description="Mark selected payments as failed")
    def mark_as_failed(self, request, queryset):
        queryset.update(payment_status='FAILED')

    def booking_link(self, obj):
        url = reverse('admin:core_eventbooking_change', args=[obj.booking.id])
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">receipt</span>'
            '<a href="{}" class="text-primary-600 hover:text-primary-900">{}</a>'
            '</div>',
            url, obj.booking.booking_reference
        )
    booking_link.short_description = "Booking"

    def amount_display(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">payments</span>'
            '<span class="font-medium">₹{}</span>'
            '</div>',
            obj.amount
        )
    amount_display.short_description = "Amount"

    def payment_badge(self, obj):
        status_config = {
            'PENDING': ('pending', 'bg-yellow-100 text-yellow-800'),
            'COMPLETED': ('check_circle', 'bg-green-100 text-green-800'),
            'FAILED': ('cancel', 'bg-red-100 text-red-800'),
            'REFUNDED': ('replay', 'bg-blue-100 text-blue-800')
        }
        icon, badge_class = status_config.get(obj.payment_status, ('help', 'bg-gray-100 text-gray-800'))
        
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-current mr-2">{}</span>'
            '<span class="px-2 py-1 text-xs font-medium rounded-full {}">{}</span>'
            '</div>',
            icon, badge_class, obj.payment_status
        )
    payment_badge.short_description = "Status"

    def payment_date(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">schedule</span>'
            '<span>{}</span>'
            '</div>',
            obj.created_at.strftime("%d %b, %Y %I:%M %p")
        )
    payment_date.short_description = "Date"

@admin.register(MenuCategory)
class MenuCategoryAdmin(ModelAdmin):
    list_display = ('name', 'items_count', 'status_badge', 'order', 'updated_at_display')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('order', 'name')

    fieldsets = [
        (
            "Category Information",
            {
                "fields": [
                    "name",
                    "description",
                    "is_active",
                ],
            },
        ),
        (
            "Display Settings",
            {
                "fields": [
                    "order",
                ],
            },
        ),
    ]

    def items_count(self, obj):
        count = obj.items.count()
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">restaurant_menu</span>'
            '<span class="text-sm">{} items</span>'
            '</div>',
            count
        )
    items_count.short_description = "Items"

    def status_badge(self, obj):
        if obj.is_active:
            badge_class = 'bg-green-100 text-green-800'
            status = 'Active'
            icon = 'check_circle'
        else:
            badge_class = 'bg-red-100 text-red-800'
            status = 'Inactive'
            icon = 'cancel'
        
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-current mr-2">{}</span>'
            '<span class="px-2 py-1 text-xs font-medium rounded-full {}">{}</span>'
            '</div>',
            icon, badge_class, status
        )
    status_badge.short_description = "Status"

    def updated_at_display(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">update</span>'
            '<span class="text-sm">{}</span>'
            '</div>',
            obj.updated_at.strftime("%d %b, %Y %I:%M %p")
        )
    updated_at_display.short_description = "Last Updated"

@admin.register(MenuItem)
class MenuItemAdmin(ModelAdmin):
    list_display = ('title', 'category_badge', 'price_display', 'status_badge', 'dietary_info', 'updated_at_display')
    list_filter = ('category', 'status', 'is_active', 'is_vegetarian', 'is_spicy')
    search_fields = ('title', 'description', 'category__name')
    ordering = ('category', 'order', 'title')

    fieldsets = [
        (
            "Basic Information",
            {
                "fields": [
                    "title",
                    "description",
                    "category",
                    "price",
                ],
            },
        ),
        (
            "Image",
            {
                "fields": [
                    "image",
                ],
            },
        ),
        (
            "Status & Attributes",
            {
                "fields": [
                    "status",
                    ("is_vegetarian", "is_spicy"),
                    "is_active",
                ],
            },
        ),
        (
            "Display Settings",
            {
                "fields": [
                    "order",
                ],
            },
        ),
    ]

    def category_badge(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">category</span>'
            '<span class="px-2 py-1 text-xs font-medium rounded-full bg-gray-100">{}</span>'
            '</div>',
            obj.category.name
        )
    category_badge.short_description = "Category"

    def price_display(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">payments</span>'
            '<span class="font-medium">₹{}</span>'
            '</div>',
            obj.price
        )
    price_display.short_description = "Price"

    def status_badge(self, obj):
        status_config = {
            'AVAILABLE': ('check_circle', 'bg-green-100 text-green-800'),
            'OUT_OF_STOCK': ('remove_shopping_cart', 'bg-red-100 text-red-800'),
            'COMING_SOON': ('upcoming', 'bg-yellow-100 text-yellow-800'),
        }
        icon, badge_class = status_config.get(obj.status)
        
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-current mr-2">{}</span>'
            '<span class="px-2 py-1 text-xs font-medium rounded-full {}">{}</span>'
            '</div>',
            icon, badge_class, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def dietary_info(self, obj):
        badges = []
        if obj.is_vegetarian:
            badges.append(('eco', 'bg-green-100 text-green-800', 'Veg'))
        if obj.is_spicy:
            badges.append(('whatshot', 'bg-red-100 text-red-800', 'Spicy'))
        
        html = '<div class="flex items-center space-x-2">'
        for icon, badge_class, text in badges:
            html += format_html(
                '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium {}">'
                '<span class="material-icons-outlined text-current mr-1" style="font-size: 14px">{}</span>'
                '{}'
                '</span>',
                badge_class, icon, text
            )
        html += '</div>'
        
        return format_html(html) if badges else '-'
    dietary_info.short_description = "Dietary Info"

    def updated_at_display(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">update</span>'
            '<span class="text-sm">{}</span>'
            '</div>',
            obj.updated_at.strftime("%d %b, %Y %I:%M %p")
        )
    updated_at_display.short_description = "Last Updated"

@admin.register(Contact)
class ContactAdmin(ModelAdmin):
    list_display = ('contact_info', 'message_preview', 'contact_date')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = [
        (
            "Contact Information",
            {
                "fields": [
                    "name",
                    "email",
                    "message",
                ],
            },
        ),
        (
            "System Fields",
            {
                "fields": ["created_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    def contact_info(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">person</span>'
            '<div>'
            '<div class="font-medium">{}</div>'
            '<div class="text-sm text-gray-500">{}</div>'
            '</div>'
            '</div>',
            obj.name,
            obj.email
        )
    contact_info.short_description = "Contact"

    def message_preview(self, obj):
        preview = obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">message</span>'
            '<span class="text-sm">{}</span>'
            '</div>',
            preview
        )
    message_preview.short_description = "Message"

    def contact_date(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">schedule</span>'
            '<span>{}</span>'
            '</div>',
            obj.created_at.strftime("%d %b, %Y %I:%M %p")
        )
    contact_date.short_description = "Date"

class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['title', 'image', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'vTextField',
                'style': 'width: 80%;',
                'placeholder': 'Enter image title here...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'vLargeTextField',
                'style': 'width: 80%; height: 100px;',
                'placeholder': 'Enter a brief description...'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'vFileField',
                'style': 'width: 80%;',
            }),
        }

@admin.register(GalleryImage)
class GalleryImageAdmin(ModelAdmin):
    list_display = ('gallery_preview', 'gallery_info', 'gallery_date', 'category_display')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    actions = ['delete_selected']
    
    fieldsets = [
        (
            "Image Information",
            {
                "fields": [
                    "title",
                    "description",
                    "category",
                    "image",
                    "image_preview_tag",
                ],
            },
        ),
        (
            "System Fields",
            {
                "fields": ["created_at"],
                "classes": ["collapse"],
            },
        ),
    ]
    
    readonly_fields = ('created_at', 'image_preview_tag')

    def category_display(self, obj):
        if obj.category:
            return format_html(
                '<div class="flex items-center">'
                '<span class="material-icons-outlined text-gray-400 mr-2">folder</span>'
                '<span>{}</span>'
                '</div>',
                obj.category.name
            )
        return format_html(
            '<div class="flex items-center text-gray-400">'
            '<span class="material-icons-outlined mr-2">folder_off</span>'
            '<span>No Category</span>'
            '</div>'
        )
    category_display.short_description = "Category"

    def gallery_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: auto; border-radius: 4px; object-fit: cover;" />',
                obj.image.url
            )
        return format_html(
            '<div class="flex items-center justify-center bg-gray-100 rounded" style="width: 100px; height: 60px;">'
            '<span class="material-icons-outlined text-gray-400">image_not_available</span>'
            '</div>'
        )
    gallery_preview.short_description = "Preview"

    def gallery_info(self, obj):
        title = obj.title or "Untitled"
        description = obj.description or "No description"
        return format_html(
            '<div class="flex flex-col">'
            '<span class="font-medium">{}</span>'
            '<span class="text-sm text-gray-500">{}</span>'
            '</div>',
            title,
            description[:100] + '...' if len(description) > 100 else description
        )
    gallery_info.short_description = "Information"

    def gallery_date(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">calendar_today</span>'
            '{}'
            '</div>',
            obj.created_at.strftime("%d %b, %Y %I:%M %p")
        )
    gallery_date.short_description = "Added On"

    def image_preview_tag(self, obj):
        if obj.image:
            return format_html(
                '<div class="mt-2">'
                '<img src="{}" style="max-width: 400px; height: auto; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />'
                '</div>',
                obj.image.url
            )
        return format_html(
            '<div class="flex items-center text-gray-400">'
            '<span class="material-icons-outlined mr-2">image_not_available</span>'
            '<span>No image uploaded</span>'
            '</div>'
        )
    image_preview_tag.short_description = "Image Preview"

    def delete_selected(self, request, queryset):
        """Custom delete action that also removes image files"""
        for obj in queryset:
            # Delete the image file if it exists
            if obj.image:
                try:
                    obj.image.delete(save=False)  # Delete the file but don't save the model yet
                except Exception:
                    pass  # Continue even if file deletion fails
            obj.delete()  # Delete the model instance
        
        self.message_user(request, f"{len(queryset)} images have been deleted successfully.")
    delete_selected.short_description = "Delete selected images"

    def delete_model(self, request, obj):
        """Override delete_model to ensure image file is deleted"""
        if obj.image:
            try:
                obj.image.delete(save=False)
            except Exception:
                pass
        obj.delete()

    def save_model(self, request, obj, form, change):
        """Override save_model to handle image replacement"""
        if change and 'image' in form.changed_data:
            # If we're changing the image, delete the old one
            try:
                old_obj = self.model.objects.get(pk=obj.pk)
                if old_obj.image:
                    old_obj.image.delete(save=False)
            except Exception:
                pass
        super().save_model(request, obj, form, change)

@admin.register(GalleryImageCategory)
class GalleryImageCategoryAdmin(ModelAdmin):
    list_display = ('name', 'image_count_display', 'status_badge', 'order', 'updated_at_display')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('order', 'name')

    fieldsets = [
        (
            "Category Information",
            {
                "fields": [
                    "name",
                    "description",
                    "is_active",
                ],
            },
        ),
        (
            "Display Settings",
            {
                "fields": [
                    "order",
                ],
            },
        ),
    ]

    def image_count_display(self, obj):
        count = obj.image_count()
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">photo_library</span>'
            '<span class="text-sm">{} images</span>'
            '</div>',
            count
        )
    image_count_display.short_description = "Images"

    def status_badge(self, obj):
        if obj.is_active:
            badge_class = 'bg-green-100 text-green-800'
            status = 'Active'
            icon = 'check_circle'
        else:
            badge_class = 'bg-red-100 text-red-800'
            status = 'Inactive'
            icon = 'cancel'
        
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-current mr-2">{}</span>'
            '<span class="px-2 py-1 text-xs font-medium rounded-full {}">{}</span>'
            '</div>',
            icon, badge_class, status
        )
    status_badge.short_description = "Status"

    def updated_at_display(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">update</span>'
            '<span class="text-sm">{}</span>'
            '</div>',
            obj.updated_at.strftime("%d %b, %Y %I:%M %p")
        )
    updated_at_display.short_description = "Last Updated"

# Customize admin site header and title
admin.site.site_header = "Club Ricky's Goa Administration"
admin.site.site_title = "Club Ricky's Goa Admin Portal"
admin.site.index_title = "Welcome to Club Ricky's Goa Admin Portal"

class TeamMemberAdmin(ModelAdmin):
    list_display = ('name', 'position', 'category_badge', 'status_badge', 'order', 'updated_at_display')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'position', 'bio')
    ordering = ('category', 'order', 'name')

    fieldsets = [
        (
            "Member Information",
            {
                "fields": [
                    "name",
                    "position",
                    "bio",
                    "category",
                    "image",
                    "image_preview_tag",
                ],
            },
        ),
        (
            "Settings",
            {
                "fields": [
                    "order",
                    "is_active",
                ],
            },
        ),
        (
            "System Fields",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]
    
    readonly_fields = ('created_at', 'updated_at', 'image_preview_tag')

    def category_badge(self, obj):
        return format_html(
            '<span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">'
            '{}'
            '</span>',
            obj.category.name
        )
    category_badge.short_description = "Category"

    def status_badge(self, obj):
        status = "Active" if obj.is_active else "Inactive"
        color = "green" if obj.is_active else "red"
        return format_html(
            '<span class="px-2 py-1 text-xs font-medium rounded-full bg-{}-100 text-{}-800">'
            '{}'
            '</span>',
            color, color, status
        )
    status_badge.short_description = "Status"

    def updated_at_display(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">schedule</span>'
            '<span>{}</span>'
            '</div>',
            obj.updated_at.strftime("%d %b, %Y %H:%M")
        )
    updated_at_display.short_description = "Last Updated"

    def image_preview_tag(self, obj):
        if obj.image:
            return format_html(
                '<div style="max-width: 300px; max-height: 300px; overflow: hidden;">'
                '<img src="{}" style="width: 100%; height: auto; object-fit: cover;" />'
                '</div>',
                obj.image.url
            )
        return "No image available"
    image_preview_tag.short_description = "Image Preview"

class TeamCategoryAdmin(ModelAdmin):
    list_display = ('name', 'member_count_display', 'status_badge', 'order', 'updated_at_display')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('order', 'name')

    fieldsets = [
        (
            "Category Information",
            {
                "fields": [
                    "name",
                    "description",
                ],
            },
        ),
        (
            "Settings",
            {
                "fields": [
                    "order",
                    "is_active",
                ],
            },
        ),
        (
            "System Fields",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]
    
    readonly_fields = ('created_at', 'updated_at')

    def member_count_display(self, obj):
        count = obj.member_count()
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">people</span>'
            '<span>{} member{}</span>'
            '</div>',
            count, 's' if count != 1 else ''
        )
    member_count_display.short_description = "Members"

    def status_badge(self, obj):
        status = "Active" if obj.is_active else "Inactive"
        color = "green" if obj.is_active else "red"
        return format_html(
            '<span class="px-2 py-1 text-xs font-medium rounded-full bg-{}-100 text-{}-800">'
            '{}'
            '</span>',
            color, color, status
        )
    status_badge.short_description = "Status"

    def updated_at_display(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">schedule</span>'
            '<span>{}</span>'
            '</div>',
            obj.updated_at.strftime("%d %b, %Y %H:%M")
        )
    updated_at_display.short_description = "Last Updated"

class JobApplicationAdmin(ModelAdmin):
    list_display = ('applicant_info', 'position_display', 'status_badge', 'resume_link', 'application_date')
    list_filter = ('position', 'status', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'experience', 'message')
    ordering = ('-created_at',)

    fieldsets = [
        (
            "Applicant Information",
            {
                "fields": [
                    "full_name",
                    "email",
                    "phone",
                    "position",
                    "status",
                ],
            },
        ),
        (
            "Application Details",
            {
                "fields": [
                    "experience",
                    "message",
                    "resume",
                ],
            },
        ),
        (
            "System Fields",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]
    
    readonly_fields = ('created_at', 'updated_at')
    actions = ["mark_under_review", "mark_for_interview", "mark_hired", "mark_rejected"]

    @admin.action(description="Mark selected applications as Under Review")
    def mark_under_review(self, request, queryset):
        queryset.update(status='under_review')

    @admin.action(description="Mark selected applications for Interview")
    def mark_for_interview(self, request, queryset):
        queryset.update(status='interview')

    @admin.action(description="Mark selected applications as Hired")
    def mark_hired(self, request, queryset):
        queryset.update(status='hired')

    @admin.action(description="Mark selected applications as Rejected")
    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected')

    def applicant_info(self, obj):
        return format_html(
            '<div class="flex flex-col">'
            '<span class="font-medium">{}</span>'
            '<span class="text-sm text-gray-500">{}</span>'
            '<span class="text-sm text-gray-500">{}</span>'
            '</div>',
            obj.full_name,
            obj.email,
            obj.phone
        )
    applicant_info.short_description = "Applicant"

    def position_display(self, obj):
        return format_html(
            '<span class="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800">'
            '{}'
            '</span>',
            obj.get_position_display()
        )
    position_display.short_description = "Position"

    def status_badge(self, obj):
        colors = {
            'new': 'blue',
            'under_review': 'yellow',
            'interview': 'purple',
            'hired': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span class="px-2 py-1 text-xs font-medium rounded-full bg-{}-100 text-{}-800 text-black">'
            '{}'
            '</span>',
            color, color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def resume_link(self, obj):
        if obj.resume:
            return format_html(
                '<a href="{}" class="text-blue-600 hover:underline" target="_blank">'
                '<span class="material-icons-outlined">description</span> View Resume'
                '</a>',
                obj.resume.url
            )
        return "No resume"
    resume_link.short_description = "Resume"

    def application_date(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">event</span>'
            '<span>{}</span>'
            '</div>',
            obj.created_at.strftime("%d %b, %Y %H:%M")
        )
    application_date.short_description = "Applied On"

admin.site.register(TeamCategory, TeamCategoryAdmin)
admin.site.register(TeamMember, TeamMemberAdmin)
admin.site.register(JobApplication, JobApplicationAdmin)
