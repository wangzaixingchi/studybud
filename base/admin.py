from django.contrib import admin
from .models import Room,Topic,Message,User
admin.site.register(User)
admin.site.register(Room)
admin.site.register(Topic)
admin.site.register(Message)
# base/admin.py

from django.contrib import admin
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')