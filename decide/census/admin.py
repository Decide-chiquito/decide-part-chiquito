from django.contrib import admin

from .models import Census


class CensusAdmin(admin.ModelAdmin):
    list_display = ('voting_id', 'voter_id', 'adscription_center')
    list_filter = ('voting_id', 'adscription_center')
    search_fields = ('voter_id', 'adscription_center')


admin.site.register(Census, CensusAdmin)
