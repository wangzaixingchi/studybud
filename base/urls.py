from django.urls import path
from . import views

from django.contrib import admin

from .views import UserSearchView

urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('register/', views.registerPage, name="register"),

    path('', views.home, name="home"),
    path('room/<str:pk>/', views.room, name="room"),
    path('room_secret/<str:pk>/', views.room, name="room_secret"),
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
    path('mute-user/<int:user_id>/', views.mute_user, name='mute-user'),
    path('unmute-user/<int:user_id>/', views.unmute_user, name='unmute-user'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_as_read,
         name='mark-notification-as-read'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/edit/<int:announcement_id>/', views.edit_announcement, name='edit_announcement'),
    path('announcements/new/', views.edit_announcement, name='new_announcement'),  # 创建新公告
    path('announcement/delete/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),

    path('add-friend/<int:user_id>/', views.add_friend, name='add_friend'),
path('room/<int:room_id>/send/', views.send_message, name='send_message'),  # 定义 send_message
    path('dm/create/<int:user_id>/', views.create_dm_room, name='create_dm_room'),
    path('search-user/', UserSearchView.as_view(), name='search-user'),  # 新增搜索用户的路由
    path('dm/room/<int:room_id>/', views.dm_room, name='dm_room'),
    path('room/<int:room_id>/messages/', views.get_messages, name='get_messages'),  # 获取消息视图
]
