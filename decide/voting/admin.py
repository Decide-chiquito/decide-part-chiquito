from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin

from .models import QuestionOption
from .models import Question
from .models import Voting
from django.contrib import messages
from .filters import StartedFilter
import csv
from django.http import HttpResponse
from django.utils.translation import gettext as _

from census.models import Census
#UPLOAD CSV
from django.urls import path
from django.shortcuts import redirect, render
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.status import (
        HTTP_409_CONFLICT as ST_409
)
from django.db.utils import IntegrityError
from django.contrib.auth.decorators import user_passes_test


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
        self.message_user(request, _("Select exactly 2 votes."), level=messages.ERROR)
    else:
        voting1, voting2 = queryset
        if voting1.id == voting2.id:
            self.message_user(request, _("The select votes are the same."), level=messages.ERROR)
        else:
            try:
                census1 = Census.objects.filter(voting_id=voting1.id)
                census2 = Census.objects.filter(voting_id=voting2.id)
                if (len(census1)>0 and len(census2)>0):
                    self.message_user(request, _("Both votes have a census"), level=messages.ERROR)
                elif(len(census1) == 0 and len(census2) == 0):
                    self.message_user(request, _("The census of both votes are empty"), level=messages.ERROR)
                elif(len(census1)>len(census2)):
                    census_to_copy = Census.objects.filter(voting_id=voting1.id)
                    for census_entry in census_to_copy:
                        Census.objects.create(voting_id=voting2.id, voter_id=census_entry.voter_id)
                    self.message_user(request, _("census successfully copied from {} to {}.").format(voting1.name, voting2.name), level=messages.SUCCESS)
                else:
                    census_to_copy = Census.objects.filter(voting_id=voting2.id)
                    for census_entry in census_to_copy:
                        Census.objects.create(voting_id=voting1.id, voter_id=census_entry.voter_id)
                    self.message_user(request, _("census successfully copied from {} to {}.").format(voting2.name, voting1.name), level=messages.SUCCESS)
            except Exception as e:
                self.message_user(request, _("Errorr in copying the census: {}").format(str(e)), level=messages.ERROR)

    copy_census_to_another_voting.short_description = _("Copy the census to other voting")

class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    inlines = [QuestionOptionInline]

@admin.register(Voting)
class VotingAdmin(ModelAdmin):
    list_display = ('name', 'start_date', 'end_date','method','seats')

    readonly_fields = ('start_date', 'end_date', 'pub_key',
                       'tally', 'postproc')
    date_hierarchy = 'start_date'
    list_filter = (StartedFilter,)
    search_fields = ('name',)

    actions = [ start, stop, tally, export_to_csv, copy_census_to_another_voting]

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]
            
            if not csv_file.name.endswith('.csv'):
                form = CsvImportForm()
                data = {"form": form,
                        "error": "El archivo no es un csv"}
                return render(request, "csv_upload.html", data)
            
            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")
            csv_data = csv_data[1:]
            data = []
            for census in csv_data:
                census = census.split(";")
                if len(census) == 2:
                    try:
                        voting_id = int(census[0].strip().replace("\r",""))
                        for voter in census[1].strip().replace("\r","").replace('"',"").split(","):
                            census = Census(voting_id=voting_id, voter_id=voter)
                            census.save()
                    except IntegrityError:
                        pass
            #Se han añadido X census
            return redirect('/admin/census/census/')

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "csv_upload.html", data)