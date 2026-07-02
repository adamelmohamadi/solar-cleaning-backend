from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            'Informations supplémentaires',
            {
                'fields': ('role',)
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Informations supplémentaires',
            {
                'fields': ('role',)
            },
        ),
    )