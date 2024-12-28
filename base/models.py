from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True, null=True)  # 确保邮箱唯一
    bio = models.TextField(null=True)
    favorites_rooms = models.ManyToManyField('Room', related_name='favorited_by', blank=True)  # 用户收藏的房间
    avatar = models.ImageField(null=True, default='avatar.svg')  # 默认头像
    score = models.IntegerField(default=0)  # 用户积分
    created = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated = models.DateTimeField(auto_now=True)  # 更新时间
    USERNAME_FIELD = 'email'  # 设置用户名字段为邮箱
    REQUIRED_FIELDS = []  # 创建用户时不需要额外字段
    is_muted = models.BooleanField(default=False)
    mute_reason = models.CharField(max_length=255, blank=True, null=True)
    mute_until = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.email  # 返回用户邮箱


class Topic(models.Model):
    name = models.CharField(max_length=200)  # 话题名称
    created = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated = models.DateTimeField(auto_now=True)  # 更新时间

    def __str__(self):
        return self.name


class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # 房间主持人
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)  # 房间话题
    name = models.CharField(max_length=200)  # 房间名称
    description = models.TextField(null=True, blank=True)  # 房间描述
    participants = models.ManyToManyField(User, related_name='participants', blank=True)  # 参与者
    created = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated = models.DateTimeField(auto_now=True)  # 更新时间
    favorites = models.ManyToManyField(User, related_name='favorite_rooms', blank=True)  # 收藏的房间

    class Meta:
        ordering = ['-updated', 'created']  # 按更新时间和创建时间排序

    def __str__(self):
        return self.name


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 发送消息的用户
    room = models.ForeignKey(Room, on_delete=models.CASCADE)  # 消息所在的房间
    body = models.TextField()  # 消息内容
    image = models.ImageField(upload_to='images/', blank=True, null=True)  # 附加图片
    video = models.FileField(upload_to='videos/', blank=True, null=True)  # 附加视频
    created = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated = models.DateTimeField(auto_now=True)  # 更新时间
    likes = models.ManyToManyField(User, related_name='liked_messages', blank=True)  # 点赞的用户

    class Meta:
        ordering = ['-updated', 'created']  # 按更新时间和创建时间排序

    def __str__(self):
        return self.body[0:50]  # 返回消息前50个字符


class Announcement(models.Model):
    title = models.CharField(max_length=200)  # 公告标题
    content = models.TextField()  # 公告内容
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # 公告作者
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated_at = models.DateTimeField(auto_now=True)  # 更新时间

    def __str__(self):
        return self.title  # 返回公告标题


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}: {self.message}"