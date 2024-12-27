from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import Room,User
from django import forms
class MyUserCreationForm(UserCreationForm):
    class Meta:
        model=User
        fields=['name','username','email','password1','password2']

class RoomForm(ModelForm):
    class Meta:
        model=Room
        fields ='__all__'
        exclude=['host','participants']


class UserForm(ModelForm):
    class Meta:
        model=User
        fields = ['avatar','name','username','email','bio']

class MessageForm(forms.Form):
    body = forms.CharField(widget=forms.TextInput(attrs={'placeholder': '发表言论'}))
    image = forms.ImageField(required=False)  # 可选的图片字段