from django.contrib import admin

from .models import Tag, Census

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name', )

class CensusAdmin(admin.ModelAdmin):
    list_display = ('voting_id', 'voter_id', 'adscription_center', 'display_tags')
    list_filter = ('voting_id', 'adscription_center', 'tags')
    search_fields = ('voter_id', 'adscription_center')

    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = 'Tags'

admin.site.register(Tag, TagAdmin)
admin.site.register(Census, CensusAdmin)
