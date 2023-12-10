from django.contrib import admin
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.contrib.auth.models import User



class UserAdmin(ModelAdmin):
     list_display = ('id','username','email','first_name','last_name','email')

admin.site.unregister(User)
admin.site.register(User,UserAdmin)