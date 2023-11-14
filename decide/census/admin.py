from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Tag, Census
from admin_auto_filters.filters import AutocompleteFilter

class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class TagAutocompleteFilter(AutocompleteFilter):
    title = 'Tag'  # El título que se mostrará para el filtro.
    field_name = 'tags'  # El nombre del campo ManyToMany en el modelo Census.

class CensusAdmin(admin.ModelAdmin):
    list_display = ('voting_id', 'voter_id', 'adscription_center', 'display_tags')
    list_filter = ('voting_id', 'adscription_center', TagAutocompleteFilter)
    search_fields = ('voter_id', 'adscription_center')
    autocomplete_fields = ['tags']

    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = 'Tags'

admin.site.register(Tag, TagAdmin)
admin.site.register(Census, CensusAdmin)
