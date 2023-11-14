from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Mixnet


@admin.register(Mixnet)
class MixnetAdmin(ModelAdmin):
    pass
