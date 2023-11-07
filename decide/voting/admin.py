from django.contrib import admin
from django.utils import timezone

from .models import QuestionOption
from .models import Question
from .models import Voting
from django.contrib import messages
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
    
def copy_census_to_another_voting(self, request, queryset):
    if queryset.count() != 2:
        self.message_user(request, "Seleccione exactamente 2 votaciones.", level=messages.ERROR)
    else:
        voting1, voting2 = queryset
        if voting1.id == voting2.id:
            self.message_user(request, "Las votaciones seleccionadas son las mismas.", level=messages.ERROR)
        else:
            try:
                census1 = Census.objects.filter(voting_id=voting1.id)
                census2 = Census.objects.filter(voting_id=voting2.id)
                if (len(census1)>0 and len(census2)>0):
                    self.message_user(request, "Ambas votaciones tienen censo", level=messages.ERROR)
                elif(len(census1) == 0 and len(census2) == 0):
                    self.message_user(request, "El censo de ambas votaciones está vacio", level=messages.ERROR)
                elif(len(census1)>len(census2)):
                    census_to_copy = Census.objects.filter(voting_id=voting1.id)
                    for census_entry in census_to_copy:
                        Census.objects.create(voting_id=voting2.id, voter_id=census_entry.voter_id)
                    self.message_user(request, "Censo copiado con éxito de {} a {}.".format(voting1.name, voting2.name), level=messages.SUCCESS)
                else:
                    census_to_copy = Census.objects.filter(voting_id=voting2.id)
                    for census_entry in census_to_copy:
                        Census.objects.create(voting_id=voting1.id, voter_id=census_entry.voter_id)
                    self.message_user(request, "Censo copiado con éxito de {} a {}.".format(voting2.name, voting1.name), level=messages.SUCCESS)
            except Exception as e:
                self.message_user(request, "Error al copiar el censo: {}".format(str(e)), level=messages.ERROR)

    copy_census_to_another_voting.short_description = "Copiar censo a otra votación"


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption


class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionOptionInline]


class VotingAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date','type','seats')
    readonly_fields = ('start_date', 'end_date', 'pub_key',
                       'tally', 'postproc')
    date_hierarchy = 'start_date'
    list_filter = (StartedFilter,)
    search_fields = ('name', )

    actions = [ start, stop, tally, export_to_csv, copy_census_to_another_voting]


admin.site.register(Voting, VotingAdmin)
admin.site.register(Question, QuestionAdmin)