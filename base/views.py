from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from .forms import MessageForm
from django.contrib import messages
from django.core.paginator import Paginator

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
            messages.error(request, '错了！！')

    return render(request, 'base/login_register.html', {'form': form})


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    print(q)
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))[0:5]

    context = {'rooms': rooms, 'topics': topics,
               'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = get_object_or_404(Room, id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if not request.user.is_authenticated:
        return redirect('/login/')

    if request.method == 'POST':
        # 获取请求中的文件
        body = request.POST.get('body')
        image = request.FILES.get('image')  # 获取上传的图片
        video = request.FILES.get('video')  # 获取上传的视频

        # 创建消息对象，保存文本和图片
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=body,
            image=image,  # 保存图片
            video=video  # 保存视频
        )

        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants
    }
    return render(request, 'base/room.html', context)


@login_required(login_url='/login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        # form =RoomForm(request.POST)
        # if form.is_valid():
        #     room =form.save(commit=False)
        #     room.host =request.user
        #     room.save()
        return redirect('home')

    context = {'form': form, "topics": topics}
    return render(request, 'base/room_form.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='/login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
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
        return redirect('home')
    context = {'form': form, "topics": topics, 'room': room}
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

    return render(request, 'home.html', {'page_obj': page_obj})