from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    list_display = ('user_info', 'contact_info', 'status_badge', 'date_joined_display')
    list_filter = ('is_active', 'is_staff', 'email_verified', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)

    fieldsets = [
        (
            "Account Information",
            {
                "fields": [
                    ("username", "email"),
                    ("password",),
                ],
            },
        ),
        (
            "Personal Information",
            {
                "fields": [
                    ("first_name", "last_name"),
                    "phone_number",
                    "profile_picture",
                    "bio",
                    "birth_date",
                    "address",
                ],
            },
        ),
        (
            "Status & Permissions",
            {
                "fields": [
                    ("is_active", "email_verified"),
                    ("is_staff", "is_superuser"),
                    "groups",
                    "user_permissions",
                ],
            },
        ),
        (
            "Important Dates",
            {
                "fields": [
                    ("date_joined", "last_login"),
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["username", "email", "password1", "password2"],
            },
        ),
    ]

    readonly_fields = ('date_joined', 'last_login')
    actions = ['verify_users', 'deactivate_users', 'activate_users']

    def user_info(self, obj):
        name = obj.get_full_name()
        if name:
            display_name = name
            secondary = obj.username
        else:
            display_name = obj.username
            secondary = None

        html = (
            '<div class="flex items-center space-x-3">'
            '<div class="flex-shrink-0">'
        )
        
        if obj.profile_picture:
            html += f'<img src="{obj.profile_picture.url}" class="h-10 w-10 rounded-full">'
        else:
            html += (
                '<div class="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">'
                '<span class="material-icons-outlined text-gray-500" style="font-size: 28px;">person</span>'
                '</div>'
            )
        
        html += (
            '</div>'
            '<div>'
            f'<div class="font-medium text-gray-900">{display_name}</div>'
        )
        
        if secondary:
            html += f'<div class="text-sm text-gray-500">@{secondary}</div>'
        
        html += '</div></div>'
        
        return format_html(html)
    user_info.short_description = "User"

    def contact_info(self, obj):
        return format_html(
            '<div class="space-y-2">'
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2" style="font-size: 20px;">email</span>'
            '<span class="text-sm">{}</span>'
            '</div>'
            '{}',
            obj.email,
            format_html(
                '<div class="flex items-center">'
                '<span class="material-icons-outlined text-gray-400 mr-2" style="font-size: 20px;">phone</span>'
                '<span class="text-sm">{}</span>'
                '</div>',
                obj.phone_number
            ) if obj.phone_number else ''
        )
    contact_info.short_description = "Contact Information"

    def status_badge(self, obj):
        if not obj.is_active:
            badge_class = 'bg-red-100 text-red-800'
            status = 'Inactive'
            icon = 'cancel'
        elif not obj.email_verified:
            badge_class = 'bg-yellow-100 text-yellow-800'
            status = 'Unverified'
            icon = 'warning'
        else:
            badge_class = 'bg-green-100 text-green-800'
            status = 'Active'
            icon = 'check_circle'
        
        badges = [
            (badge_class, status, icon)
        ]
        
        if obj.is_staff:
            badges.append(('bg-blue-100 text-blue-800', 'Staff', 'admin_panel_settings'))
        if obj.is_superuser:
            badges.append(('bg-purple-100 text-purple-800', 'Admin', 'security'))
        
        html = '<div class="flex items-center space-x-2">'
        for badge_class, status, icon in badges:
            html += format_html(
                '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
                '<span class="material-icons-outlined text-current mr-1" style="font-size: 16px;">{}</span>'
                '{}'
                '</span>',
                badge_class, icon, status
            )
        html += '</div>'
        
        return format_html(html)
    status_badge.short_description = "Status"

    def date_joined_display(self, obj):
        return format_html(
            '<div class="flex items-center">'
            '<span class="material-icons-outlined text-gray-400 mr-2" style="font-size: 20px;">event</span>'
            '<span class="text-sm">{}</span>'
            '</div>',
            obj.date_joined.strftime("%d %b, %Y")
        )
    date_joined_display.short_description = "Joined"

    @admin.action(description="Verify selected users")
    def verify_users(self, request, queryset):
        queryset.update(email_verified=True)

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        queryset.update(is_active=True) 