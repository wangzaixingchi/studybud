from django.contrib import admin
from django.utils import timezone

from .models import Room,Topic,Message,User
admin.site.register(Room)
admin.site.register(Topic)
admin.site.register(Message)
# base/admin.py

from django.contrib import admin

admin.site.site_header = "聊天室管理"
admin.site.site_title = "网站后台"
admin.site.index_title = "欢迎来到聊天室管理后台"
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

from django.contrib import admin
from django.templatetags.static import static

class CustomAdminSite(admin.AdminSite):
    site_header = "我的网站管理"
    site_title = "网站后台"
    index_title = "欢迎来到网站管理后台"

    def get_urls(self):
        urls = super().get_urls()
        return urls

    def get_extra_context(self, request):
        return {
            'custom_css': static('your_app/css/custom_admin.css'),
        }

admin_site = CustomAdminSite(name='custom_admin')