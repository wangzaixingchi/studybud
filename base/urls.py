from django.urls import path
from . import views

from django.contrib import admin
urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('register/', views.registerPage, name="register"),

    path('', views.home, name="home"),
    path('room/<str:pk>/', views.room, name="room"),
    path('profile/<str:pk>/', views.userProfile, name="user-profile"),
    path('create-room/', views.createRoom, name="create-room"),
    path('update-room/<str:pk>/', views.updateRoom, name="update-room"),
    path('delete-room/<str:pk>/', views.deleteRoom, name="delete-room"),
    path('delete-message/<str:pk>/', views.deleteMessage, name="delete-message"),

    path('update-user/', views.updateUser, name="update-user"),
    path('topics/', views.topicsPage, name="topics"),
    path('activity/', views.activityPage, name="activity"),
    path('game/', views.game, name="game"),
    path('update_score/', views.update_score, name="update_score"),
    path('get_ranklist/', views.get_ranklist, name='get_ranklist'),
    path('room_list_view/', views.room_list_view, name='room_list_view'),
    path('room/<int:room_id>/toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('message/<int:message_id>/toggle-like/', views.toggle_like, name='toggle_like'),
    path('my-favorites/', views.my_favorites, name='my-favorites'),

]
