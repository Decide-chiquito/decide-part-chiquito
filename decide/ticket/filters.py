from typing import Any
from django.contrib.admin import SimpleListFilter
from django.db.models.query import QuerySet

class StatusFilter(SimpleListFilter):
    title = 'status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [
            ('PENDING', 'Pending'),
            ('SOLVED', 'Solved'),
            ('REJECTED', 'Rejected'),
        ]
    def queryset(self, request, queryset):
        value = self.value()
        if value == 'PENDING':
            return queryset.filter(status='PENDING')
        elif value == 'SOLVED':
            return queryset.filter(status='SOLVED')
        elif value == 'REJECTED':
            return queryset.filter(status='REJECTED')
    
        