from django.contrib import admin
from django.utils import timezone

from .models import Room,Topic,Message,User
admin.site.register(Room)
admin.site.register(Topic)
admin.site.register(Message)
# base/admin.py

from django.contrib import admin
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_muted', 'mute_reason', 'mute_until')
    search_fields = ('username', 'email')

    def save_model(self, request, obj, form, change):
        if obj.mute_until and obj.mute_until > timezone.now():
            obj.is_muted = True
        else:
            obj.is_muted = False
        super().save_model(request, obj, form, change)

admin.site.register(User, UserAdmin)