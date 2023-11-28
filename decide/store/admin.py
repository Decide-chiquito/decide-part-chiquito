from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Vote


@admin.register(Vote)
class VoteAdmin(ModelAdmin):
    list_display = ('voting_id', 'voter_id', 'question_id', 'voted')
    list_filter = ('voting_id', 'voter_id', 'question_id')
    search_fields = ('voting_id', 'voter_id', 'question_id')
    ordering = ('-voted',)
    readonly_fields = ('voted',)
    fieldsets = (
        (None, {
            'fields': ('voting_id', 'voter_id', 'question_id', 'voted')
        }),
        ('Votes', {
            'fields': ('a', 'b')
        }),
    )
