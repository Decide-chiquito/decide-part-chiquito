from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from unfold.admin import ModelAdmin

from .models import Ticket, TicketStatus
from .filters import StatusFilter



def solve_ticket(ModelAdmin, request, queryset):
    for t in queryset.all():
        t.status = 'SOLVED'
        t.save()

def reject_ticket(ModelAdmin, resquest, queryset):
    queryset.update(status='REJECTED')


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = ('title', 'description', 'status')

    list_filter = (StatusFilter,)
    search_fields = ('title','status')

    actions = [solve_ticket, reject_ticket]




