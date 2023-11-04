from django.contrib import admin
from django.utils import timezone

from .models import QuestionOption
from .models import Question
from .models import Voting

from .filters import StartedFilter

import csv
from django.http import HttpResponse

from census.models import Census


def start(modeladmin, request, queryset):
    for v in queryset.all():
        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()


def stop(ModelAdmin, request, queryset):
    for v in queryset.all():
        v.end_date = timezone.now()
        v.save()


def tally(ModelAdmin, request, queryset):
    for v in queryset.filter(end_date__lt=timezone.now()):
        token = request.session.get('auth-token', '')
        v.tally_votes(token)

def export_to_csv(ModelAdmin, request, queryset):
    if queryset:
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="census.csv"'},
            )
        for v in queryset:       
            voting_name = v.name
            voting_id = v.id

            writer = csv.writer(response)
            writer.writerow(["Voting:", str(voting_name)])
            writer.writerow(["Voting Id:", str(voting_id)])
            
            census = Census.objects.filter(voting_id=voting_id)
            if census:
                for c in census:
                    voter_id = c.voter_id
                    writer.writerow(["Voter Id:", voter_id])
            else:
                writer.writerow(["Voter Id:", "No Census yet"])
            writer.writerow([])
            
        return response


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption


class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionOptionInline]


class VotingAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    readonly_fields = ('start_date', 'end_date', 'pub_key',
                       'tally', 'postproc')
    date_hierarchy = 'start_date'
    list_filter = (StartedFilter,)
    search_fields = ('name', )

    actions = [ start, stop, tally, export_to_csv ]


admin.site.register(Voting, VotingAdmin)
admin.site.register(Question, QuestionAdmin)
