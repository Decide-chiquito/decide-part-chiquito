from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Census


@admin.register(Census)
class CensusAdmin(ModelAdmin):
    list_display = ('voting_id', 'voter_id')
    list_filter = ('voting_id', )
    search_fields = ('voter_id', )


