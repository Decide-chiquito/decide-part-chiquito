from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Auth, Key


@admin.register(Auth)
class AuthAdmin(ModelAdmin):
    pass


@admin.register(Key)
class KeyAdmin(ModelAdmin):
    pass
