from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Vote


@admin.register(Vote)
class VoteAdmin(ModelAdmin):
    pass
