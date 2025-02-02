import hashlib
from datetime import datetime

from cryptography.fernet import Fernet
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST

from .models import Room, Topic, Message, User, Announcement, DirectMessageRoom, Profile, RoomHistory
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from .forms import MessageForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Announcement
from .forms import AnnouncementForm
from .models import DirectMessage, DirectMessageRoom


# 获取房间信息
def get_room_info(room):
    room_messages = room.message_set.all()
    participants = room.participants.all()
    return room_messages, participants


# 校验密码
def check_password(room, entered_password):
    hashed_password = hashlib.md5((entered_password + 'wangzaixiaoqi').encode()).hexdigest()
    return hashed_password == room.encryption_key


# 登录
def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, '用户不存在!')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, '用户名错误!')
    context = {'page': page}
    return render(request, 'base/login_register.html', context)


# 退出登录
def logoutUser(request):
    logout(request)
    return redirect('home')


# 注册页面
def registerPage(request):
    form = MyUserCreationForm()
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, '用户已存在或二次密码不匹配!')

    return render(request, 'base/login_register.html', {'form': form})


# 主页
def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    print(q)
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    announcements = Announcement.objects.all().order_by('-created_at')[:5]
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))[0:5]

    context = {'rooms': rooms, 'topics': topics,
               'room_count': room_count, 'room_messages': room_messages, 'announcements': announcements}
    return render(request, 'base/home.html', context)


# 房间页面
@login_required(login_url='/login/')
def room(request, pk):
    room = get_object_or_404(Room, id=pk)
    room_messages, participants = get_room_info(room)
    room_history, created = RoomHistory.objects.get_or_create(
        user=request.user,
        room=room,
        defaults={'timestamp': timezone.now()}
    )
    if not created:
        # 如果记录已存在，更新时间戳
        room_history.timestamp = timezone.now()
        room_history.save()
    # 检查房间是否加密
    if room.is_encrypted:
        # 检查用户是否已通过密码验证
        if request.session.get(f'room_access_{room.id}', False):
            if request.method == 'POST':
                return handle_message_post(request, room)

            context = {
                'room': room,
                'room_messages': room_messages,
                'participants': participants,
            }
            return render(request, 'base/room.html', context)

        else:
            # 处理密码输入
            if request.method == 'POST':
                entered_password = request.POST.get('encryption_key')

                if check_password(room, entered_password):
                    request.session[f'room_access_{room.id}'] = True  # 设置当前房间的访问权限
                    return redirect('room', pk=room.id)  # 重定向到当前房间页面
                else:
                    error_message = "密码错误，请重试。"

            context = {
                'room': room,
            }
            return render(request, 'base/room_secret.html', context)  # 跳转到房间密码输入页面

    # 处理发送消息
    if request.method == 'POST':
        return handle_message_post(request, room)

    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants,
    }
    return render(request, 'base/room.html', context)


# 发送信息
def handle_message_post(request, room):
    """处理消息发送的逻辑"""
    body = request.POST.get('body')
    image = request.FILES.get('image')
    video = request.FILES.get('video')
    # 检查 body、image 和 video 是否都为空
    if not body and not image and not video:
        # 直接返回，不处理消息
        return
    Message.objects.create(
        user=request.user,
        room=room,
        body=body,
        image=image,
        video=video
    )
    room.participants.add(request.user)
    return redirect('room', pk=room.id)


from django.db import transaction

# 房间收藏
from django.http import JsonResponse

#浏览记录

class RoomHistoryView(View):
    def get(self, request):
        if request.user.is_authenticated:
            room_history = RoomHistory.objects.filter(user=request.user).values('room__id','room__name', 'timestamp')
            paginator = Paginator(room_history, 5)  # 每页显示 10 条记录

            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            history_list = list(page_obj)  # 转换为列表以便于 JSON 序列化

            return JsonResponse({
                'status': 'success',
                'data': history_list,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            })

        return JsonResponse({'status': 'error', 'message': '未登录'})
def toggle_favorite(request, room_id):
    if request.method == 'POST' and request.user.is_authenticated:
        room = get_object_or_404(Room, id=room_id)

        # 检查用户是否已收藏该房间
        if request.user in room.favorites.all():
            room.favorites.remove(request.user)  # 取消收藏
            favorited = False
        else:
            room.favorites.add(request.user)  # 添加收藏
            favorited = True

        return JsonResponse({'favorited': favorited})


# 评论点赞
def toggle_like(request, message_id):
    if request.method == 'POST':
        message = get_object_or_404(Message, id=message_id)
        if request.user in message.likes.all():
            message.likes.remove(request.user)
        else:
            message.likes.add(request.user)

        return JsonResponse({'liked': request.user in message.likes.all()})
    return JsonResponse({'error': 'Invalid request'}, status=400)


# 我的收藏
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Room


def my_favorites(request):
    if request.user.is_authenticated:
        favorites = request.user.favorite_rooms.all()  # 获取当前用户收藏的所有房间
        favorite_rooms = []

        for room in favorites:
            favorite_rooms.append({
                'id': room.id,
                'name': room.name,
                'host': room.host.username,
                'host_avatar': room.host.avatar.url if room.host.avatar else None,
                'created': room.created.isoformat(),  # 使用 ISO 格式
                'participants_count': room.participants.count(),
                'topic': room.topic.name if room.topic else '无主题',  # 处理可能没有主题的情况
            })

        return JsonResponse({'favorites': favorite_rooms})
    else:
        return JsonResponse({'favorites': []})  # 如果用户未登录，返回空列表


# 创建房间
@login_required(login_url='/login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        # 检查是否需要加密
        is_encrypted = request.POST.get('is_encrypted') == 'on'  # 对应复选框的值
        encryption_key = None

        if is_encrypted:
            # 生成 MD5 哈希，使用盐值增强安全性
            encryption_key = hashlib.md5((request.POST.get('encryption_key') + 'wangzaixiaoqi').encode()).hexdigest()

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            encryption_key=encryption_key,  # 存储 MD5 哈希
            is_encrypted=is_encrypted  # 设置加密状态
        )
        return redirect('home')  # 创建成功后重定向到主页

    context = {'form': form, "topics": topics}
    return render(request, 'base/room_form.html', context)


# 用户资料
@login_required(login_url='/login/')
def userProfile(request, pk):
    user = User.objects.get(id=pk)
    profile, created = Profile.objects.get_or_create(user=user)  # 确保有Profile实例

    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    favorites = user.favorites_rooms.all()  # 获取用户的收藏房间
    followers_count = profile.followers_count
    followers = profile.followers.all()  # 获取关注
    following_count = profile.followers.count()  # 关注数量
    paginator = Paginator(followers, 5)  # 每页显示5个关注者
    page_number = request.GET.get('page')
    followers_page = paginator.get_page(page_number)
    room_history = RoomHistory.objects.filter(user=user)  # 获取房间历史记录
    context = {
        'user': user,
        'rooms': rooms,
        'room_messages': room_messages,
        'topics': topics,
        'favorites': favorites,
        'following_count': following_count,
        'followers_count': followers_count,
        'followers': followers,
        'followers': followers_page,
        'followers_page': followers_page,
        'room_history': room_history,

    }
    return render(request, 'base/profile.html', context)


# 更新房间
@login_required(login_url='/login')
def updateRoom(request, pk):
    room = get_object_or_404(Room, id=pk)  # 使用 get_object_or_404 获取房间
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('NO!!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')

        # 检查是否需要更新加密
        is_encrypted = request.POST.get('is_encrypted') == 'on'  # 对应复选框的值
        encryption_key = None

        if is_encrypted:
            encryption_key = hashlib.md5((request.POST.get('encryption_key') + 'wangzaixiaoqi').encode()).hexdigest()

        room.is_encrypted = is_encrypted  # 更新加密状态
        room.encryption_key = encryption_key if is_encrypted else None  # 存储加密密钥

        room.save()  # 保存房间更改
        return redirect('home')  # 更新成功后重定向到主页

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)


# 删除房间
@login_required(login_url='/login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    if request.user != room.host:
        return HttpResponse('NO!!!')
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


# 删除信息
@login_required(login_url='/login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    if request.user != message.user:
        return HttpResponse('NO!!!')
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='/login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=request.user)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    context = {'form': form}
    return render(request, 'base/update-user.html', context)


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics': topics}
    return render(request, 'base/topics.html', context)


def activityPage(request):
    room_messages = Message.objects.all()[0:5]
    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context)


@login_required(login_url='/login')
def game(request):
    return render(request, 'base/game.html')


@login_required(login_url='/login')
def update_score(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        new_score = request.POST.get('score')

        # 获取用户对象
        user = get_object_or_404(User, id=id)

        # 更新分数
        if new_score.isdigit():  # 确保分数是数字
            user.score = int(new_score)
            user.save()
            return redirect('home')  # 重定向到主页或其他页面
        else:
            return HttpResponse("无效的分数", status=400)

    return HttpResponse("不支持的请求方法", status=405)


@login_required(login_url='/login')
def get_ranklist(request):
    if request.method == 'GET':
        # 获取所有用户并按分数降序排序，仅获取前 5 名
        users = User.objects.all().order_by('-score')[:5]

        # 构建排行榜数据
        ranklist = []
        for rank, user in enumerate(users, start=1):
            ranklist.append({
                'rank': rank,
                'username': user.username,  # 假设 User 模型有 username 字段
                'score': user.score,
                'avatar': user.avatar.url if user.avatar else 'https://via.placeholder.com/40'  # 添加头像链接
            })

        return JsonResponse(ranklist, safe=False)  # 返回 JSON 响应

    return JsonResponse({"error": "不支持的请求方法"}, status=405)


def room_list_view(request):
    rooms = Room.objects.all()  # 获取所有房间
    paginator = Paginator(rooms, 2)  # 每页显示2个房间

    page_number = request.GET.get('page')  # 获取当前页码
    page_obj = paginator.get_page(page_number)  # 获取当前页的房间对象

    return render(request, 'base/home.html', {'page_obj': page_obj})


@login_required(login_url='/login')
def mute_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if not request.user.is_superuser:
            return redirect('not-authorized')  # 或者处理未授权的逻辑
        mute_until = request.POST.get('mute_until')  # 期望格式为 'YYYY-MM-DD HH:MM'
        mute_reason = request.POST.get('mute_reason')
        user.mute_until = timezone.datetime.strptime(mute_until, '%Y-%m-%d %H:%M')
        user.mute_reason = mute_reason
        user.is_muted = True
        user.save()
        return redirect('user-profile', user_id=user.id)

    return render(request, 'base/mute_user.html', {'user': user})


from django.contrib import messages
from .models import Notification


@login_required(login_url='/login')
def mute_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        mute_until = request.POST.get('mute_until')  # 期望格式为 'YYYY-MM-DD HH:MM'
        mute_reason = request.POST.get('mute_reason')

        if mute_until:
            try:
                # 使用正确的格式解析
                mute_until_datetime = datetime.strptime(mute_until, '%Y-%m-%dT%H:%M')

                # 转换为 Django 的 timezone-aware 对象
                mute_until_datetime = timezone.make_aware(mute_until_datetime)

                # 保存到用户对象
                user.mute_until = mute_until_datetime  # 直接使用已转换的时间
                user.mute_reason = mute_reason
                user.is_muted = True
                user.save()
            except ValueError as e:
                print(f"解析错误: {e}")
        else:
            print("未获取到 mute_until 值")

        # 添加通知
        notification_message = f"您已被禁言至 {mute_until}，原因: {mute_reason}"
        Notification.objects.create(user=user, message=notification_message)

        messages.success(request, f"{user.username} 已被禁言。")
        return redirect('user-profile', pk=str(user.id))

    return render(request, 'base/mute_user.html', {'user': user})


@login_required(login_url='/login')
def unmute_user(request, user_id):
    user = get_object_or_404(User, id=user_id)  # 获取用户对象

    # 检查用户是否是管理员
    if request.user.is_superuser:
        user.is_muted = False  # 将用户的禁言状态设置为 False
        user.save()  # 保存更改

        # 添加通知
        notification_message = f"您已被取消禁言，您现在可以再次发言。"
        Notification.objects.create(user=user, message=notification_message)

        messages.success(request, f"{user.username} 已成功取消禁言。")
    else:
        messages.error(request, "您没有权限取消禁言。")

    return redirect('user-profile', pk=str(user.id))  # 重定向到用户资料页面

@login_required(login_url='/login')
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')  # 假设您有一个显示通知的页面



@login_required(login_url='/login')  # 确保用户已登录
def notifications_view(request):
    # 获取当前用户的所有通知
    notifications = request.user.notification_set.all().order_by('-timestamp')  # 按时间降序排列

    # 设置每页显示的通知数量
    paginator = Paginator(notifications, 5)  # 每页显示5个通知

    # 获取当前页码
    page_number = request.GET.get('page')  # 从URL获取页码
    notifications_page = paginator.get_page(page_number)  # 获取当前页的通知

    # 渲染通知模板，传递分页通知数据
    return render(request, 'base/notifications.html', {'notifications': notifications_page})


# 公告列表
def announcement_list(request):
    announcements = Announcement.objects.all()
    return render(request, 'base/announcement_list.html', {'announcements': announcements})


# 编辑公告
def edit_announcement(request, announcement_id=None):
    if announcement_id:
        announcement = get_object_or_404(Announcement, id=announcement_id)
    else:
        announcement = None

    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            new_announcement = form.save(commit=False)  # 不立即保存
            new_announcement.author = request.user  # 设置作者为当前用户
            form.save()
            return redirect('announcement_list')  # 编辑或创建成功后重定向
    else:
        form = AnnouncementForm(instance=announcement)

    return render(request, 'base/edit_announcement.html', {'form': form, 'announcement': announcement})


# 删除公告
@require_POST
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    return redirect('announcement_list')  # 重定向到公告列表页面


# 添加好友
@login_required(login_url='/login')
def add_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)

    if request.user == friend:
        messages.error(request, "不能添加自己为好友。")
    else:
        request.user.userprofile.friends.add(friend)
        messages.success(request, f"已成功添加 {friend.username} 为好友。")

    return redirect(request.META.get('HTTP_REFERER', 'home'))  # 返回到上一页或主页


# 私聊
@login_required(login_url='/login')
def create_dm_room(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    # 确保房间创建是双向的
    room, created = DirectMessageRoom.objects.get_or_create(
        user1=request.user,
        user2=other_user,
    )

    if not created:  # 如果房间已经存在，尝试获取另一种组合
        room, created = DirectMessageRoom.objects.get_or_create(
            user1=other_user,
            user2=request.user,
        )

    return redirect('dm_room', room_id=room.id)


# 私聊
@login_required(login_url='/login')
def dm_room(request, room_id):
    room = get_object_or_404(DirectMessageRoom, id=room_id)
    messages = room.messages.all()
    # 获取 user1 和 user2
    user1 = room.user1
    user2 = room.user2
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')  # 获取上传的图片
        if content or image:  # 只在内容或图片不为空时创建消息
            DirectMessage.objects.create(room=room, sender=request.user, content=content, image=image)

            return redirect('dm_room', room_id=room.id)

    return render(request, 'base/dm_room.html', {'room': room, 'messages': messages})



def send_message(request, room_id):
    room = get_object_or_404(DirectMessageRoom, id=room_id)
    user1 = room.user1
    user2 = room.user2

    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')  # 获取上传的图片

        # 查找当前用户和目标用户之间的房间
        room2 = DirectMessageRoom.objects.filter(
            (Q(user1=user2) & Q(user2=user1)) | (Q(user1=user1) & Q(user2=user2))
        ).first()

        if content or image:  # 只在内容或图片不为空时创建消息
            if room2 is not None:
                DirectMessage.objects.create(room=room2, sender=request.user, content=content, image=image)
            else:
                return JsonResponse({'status': 'error', 'message': '房间不存在'})

        # 创建当前房间的消息
        message = DirectMessage.objects.create(room=room, sender=request.user, content=content, image=image)

        # 返回 JSON 响应
        return JsonResponse({
            'sender': message.sender.username,
            'sender_avatar': message.sender.avatar.url if message.sender.avatar else None,  # 发送者头像
            'content': message.content,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M'),
            'image': message.image.url if message.image else None,
        })

    return JsonResponse({'status': 'error', 'message': '请求方法不正确'})

@login_required(login_url='/login')
def get_messages(request, room_id):
    room = get_object_or_404(DirectMessageRoom, id=room_id)
    messages = room.directmessage_set.all().select_related('sender')  # 获取房间的所有消息
    message_list = []

    for message in messages:
        message_list.append({
            'sender': message.sender.username,
            'content': message.content,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M'),
            'image': message.image.url if message.image else None,
            'is_mine': message.sender == request.user,  # 标识消息是否是当前用户发送
        })

    return JsonResponse({'messages': message_list})


def fetch_messages(request, room_id):
    messages = Message.objects.filter(room_id=room_id).order_by('-created_at')[:10]  # 获取最新的10条消息
    data = {
        'messages': [
            {
                'content': message.content,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'image': message.image.url if message.image else None,
                'sender': {
                    'username': message.sender.username,
                    'avatar': message.sender.avatar.url,
                }
            }
            for message in messages
        ]
    }
    return JsonResponse(data)


class UserSearchView(View):
    def get(self, request):
        username = request.GET.get('user', '')
        if username:
            users = User.objects.filter(username__icontains=username)  # 使用模糊查询
            paginator = Paginator(users, 5)  # 每页显示10个用户
            page_number = request.GET.get('page')
            users_page = paginator.get_page(page_number)

            if users_page:
                return render(request, 'base/user_search_results.html', {
                    'users': users_page,
                    'query': username,
                })  # 显示结果
            else:
                return render(request, 'base/user_not_found.html')  # 用户未找到
        return redirect('home')  # 如果没有提供用户名，重定向回主页
User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
@login_required(login_url='/login')
def follow_user(request, user_id):
    if request.method == 'POST':
        user_to_follow = get_object_or_404(User, id=user_id)

        # 确保当前用户未关注该用户
        if request.user != user_to_follow and user_to_follow not in request.user.profile.followers.all():
            request.user.profile.followers.add(user_to_follow)
            return JsonResponse({'status': 'success', 'action': 'follow', 'user_id': user_id})

    return JsonResponse({'status': 'error', 'message': 'Could not follow user.'})
@login_required(login_url='/login')
def unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)
    request.user.profile.followers.remove(user_to_unfollow)
    return JsonResponse({'status': 'success', 'action': 'unfollow', 'user_id': user_id})
@login_required

def disable_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.user.is_superuser or request.user == room.host:
        room.is_disabled = True
        room.save()

        # 发送通知
        notification_message = f"房间 '{room.name}' 已被禁用。"
        Notification.objects.create(user=room.host, message=notification_message)

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=403)
@login_required
def enable_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.user.is_superuser or request.user == room.host:
        room.is_disabled = False
        room.save()

        # 发送解禁通知
        notification_message = f"房间 '{room.name}' 已被解禁。"
        Notification.objects.create(user=room.host, message=notification_message)

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=403)


def disable_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.method == 'POST':
        room.is_disabled = True  # 禁用房间
        room.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)
