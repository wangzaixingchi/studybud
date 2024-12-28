import hashlib
from datetime import datetime

from cryptography.fernet import Fernet
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone

from .models import Room, Topic, Message, User, Announcement
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from .forms import MessageForm
from django.contrib import messages
from django.core.paginator import Paginator


def get_room_info(room):
    room_messages = room.message_set.all()
    participants = room.participants.all()
    return room_messages, participants


def check_password(room, entered_password):
    hashed_password = hashlib.md5((entered_password + 'wangzaixiaoqi').encode()).hexdigest()
    return hashed_password == room.encryption_key


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


def logoutUser(request):
    logout(request)
    return redirect('home')


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


def room(request, pk):
    room = get_object_or_404(Room, id=pk)

    if not request.user.is_authenticated:
        return redirect('/login/')

    room_messages, participants = get_room_info(room)

    # 检查房间是否加密
    if room.is_encrypted:
        # 检查用户是否已通过密码验证
        if request.session.get(f'room_access_{room.id}', False):
            # 用户已验证，允许访问
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

    # 如果房间未加密，允许用户发送消息
    if request.method == 'POST':
        return handle_message_post(request, room)

    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants,
    }
    return render(request, 'base/room.html', context)

def handle_message_post(request, room):
    """处理消息发送的逻辑"""
    body = request.POST.get('body')
    image = request.FILES.get('image')
    video = request.FILES.get('video')
    # 检查 body、image 和 video 是否都为空
    if not body and not image and not video:
        # 直接返回，不处理消息
        return redirect('room', pk=room.id)
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


def toggle_favorite(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.user.is_authenticated:
        with transaction.atomic():
            if request.user in room.favorites.all():
                room.favorites.remove(request.user)
            else:
                room.favorites.add(request.user)
            if room in request.user.favorites_rooms.all():  # 使用 favorites_rooms
                request.user.favorites_rooms.remove(room)
            else:
                request.user.favorites_rooms.add(room)
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def toggle_like(request, message_id):
    if request.method == 'POST':
        message = get_object_or_404(Message, id=message_id)
        if request.user in message.likes.all():
            message.likes.remove(request.user)
        else:
            message.likes.add(request.user)

        return JsonResponse({'liked': request.user in message.likes.all()})
    return JsonResponse({'error': 'Invalid request'}, status=400)


def my_favorites(request):
    # 获取当前用户的收藏房间
    favorites = request.user.favorites.all()  # 获取当前用户收藏的所有房间
    return render(request, 'base/feed_component_favorite.html', {'favorites': favorites})


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


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    favorites = user.favorites_rooms.all()  # 获取用户的收藏房间
    context = {
        'user': user,
        'rooms': rooms,
        'room_messages': room_messages,
        'topics': topics,
        'favorites': favorites}
    return render(request, 'base/profile.html', context)


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


@login_required(login_url='/login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    if request.user != room.host:
        return HttpResponse('NO!!!')
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


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
    paginator = Paginator(rooms, 2)  # 每页显示 10 个房间

    page_number = request.GET.get('page')  # 获取当前页码
    page_obj = paginator.get_page(page_number)  # 获取当前页的房间对象

    return render(request, 'base/home.html', {'page_obj': page_obj})


@login_required
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


@login_required
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


@login_required
def unmute_user(request, user_id):
    user = get_object_or_404(User, id=user_id)  # 获取用户对象

    # 检查用户是否是管理员
    if request.user.is_superuser:
        user.is_muted = False  # 将用户的禁言状态设置为 False
        user.save()  # 保存更改

        messages.success(request, f"{user.username} 已成功取消禁言。")
    else:
        messages.error(request, "您没有权限取消禁言。")

    return redirect('user-profile', pk=str(user.id))  # 重定向到用户资料页面


@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')  # 假设您有一个显示通知的页面


@login_required  # 确保用户已登录
def notifications_view(request):
    # 获取当前用户的通知
    notifications = request.user.notification_set.all()
    # 渲染通知模板，传递通知数据
    return render(request, 'base/notifications.html', {'notifications': notifications})
