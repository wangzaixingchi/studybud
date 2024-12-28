from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import Room, User
from django import forms
from django.contrib import admin


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'password1', 'password2']


class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['avatar', 'name', 'username', 'email', 'bio']


class MessageForm(forms.Form):
    body = forms.CharField(widget=forms.TextInput(attrs={'placeholder': '发表言论'}))
    image = forms.ImageField(required=False)  # 可选的图片字段


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'


class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm

    def save_model(self, request, obj, form, change):
        # 如果禁言时间设置了，并且在当前时间之后，禁言用户
        if obj.mute_until and obj.mute_until > timezone.now():
            obj.is_muted = True
        else:
            obj.is_muted = False
        super().save_model(request, obj, form, change)


from django import forms
from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content']  # 包含标题和内容字段
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入公告标题'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '请输入公告内容', 'rows': 5}),
        }
        labels = {
            'title': '公告标题',
            'content': '公告内容',
        }
