from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from unfold.admin import ModelAdmin
from .models import Event, EventBooking, Payment, MenuCategory, MenuItem, Contact

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
                    ("max_stag_bookings", "max_couple_bookings"),
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
            obj.start_time.strftime('%I:%M %p'),
            obj.end_time.strftime('%I:%M %p')
        )
    event_time.short_description = "Time"

    def seats_status(self, obj):
        percentage = (obj.available_seats / obj.total_seats) * 100
        if percentage > 60:
            color_class = 'bg-green-100 text-green-800'
            icon = 'check_circle'
        elif percentage > 30:
            color_class = 'bg-yellow-100 text-yellow-800'
            icon = 'warning'
        else:
            color_class = 'bg-red-100 text-red-800'
            icon = 'error'
        
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-current mr-2">{}</span>'
            '<span class="px-2 py-1 text-xs font-medium rounded-full {}">'
            '{}/{}</span></div>',
            icon, color_class, obj.available_seats, obj.total_seats
        )
    seats_status.short_description = "Seats"

    def price_display(self, obj):
        return format_html(
            '<div class="space-y-1">'
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">person</span>'
            '<span>Stag: ₹{}</span>'
            '</div>'
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2">people</span>'
            '<span>Couple: ₹{}</span>'
            '</div>'
            '</div>',
            obj.stag_fee, obj.couple_fee
        )
    price_display.short_description = "Pricing"

    def status_badge(self, obj):
        if not obj.is_active:
            badge_class = 'bg-red-100 text-red-800'
            status = 'Inactive'
            icon = 'cancel'
        elif obj.date < timezone.now().date():
            badge_class = 'bg-gray-100 text-gray-800'
            status = 'Past'
            icon = 'history'
        else:
            badge_class = 'bg-green-100 text-green-800'
            status = 'Active'
            icon = 'check_circle'
        
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-current mr-2">{}</span>'
            '<span class="px-2 py-1 text-xs font-medium rounded-full {}">{}</span>'
            '</div>',
            icon, badge_class, status
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
            '<div class="flex items-center">'
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
            '<div class="flex items-center">'
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

# Customize admin site header and title
admin.site.site_header = "Club Ricky's Goa Administration"
admin.site.site_title = "Club Ricky's Goa Admin Portal"
admin.site.index_title = "Welcome to Club Ricky's Goa Admin Portal"
