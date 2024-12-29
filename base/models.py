from cryptography.fernet import Fernet
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    name = models.CharField(max_length=200, null=True, verbose_name='姓名')
    email = models.EmailField(unique=True, null=True, verbose_name='邮箱')  # 确保邮箱唯一
    bio = models.TextField(null=True, verbose_name='个人简介')
    favorites_rooms = models.ManyToManyField('Room', related_name='favorited_by', blank=True,
                                             verbose_name='收藏的房间')  # 用户收藏的房间
    avatar = models.ImageField(null=True, default='avatar.svg', verbose_name='头像')  # 默认头像
    score = models.IntegerField(default=0, verbose_name='积分')  # 用户积分
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')  # 创建时间
    updated = models.DateTimeField(auto_now=True, verbose_name='更新时间')  # 更新时间
    USERNAME_FIELD = 'email'  # 设置用户名字段为邮箱
    REQUIRED_FIELDS = []  # 创建用户时不需要额外字段
    is_muted = models.BooleanField(default=False, verbose_name='是否静音')
    mute_reason = models.CharField(max_length=255, blank=True, null=True, verbose_name='静音原因')
    mute_until = models.DateTimeField(blank=True, null=True, verbose_name='静音至')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户列表'

    def __str__(self):
        return self.email  # 返回用户邮箱


class Topic(models.Model):
    name = models.CharField(max_length=200, verbose_name='话题名称')  # 话题名称
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')  # 创建时间
    updated = models.DateTimeField(auto_now=True, verbose_name='更新时间')  # 更新时间

    class Meta:
        verbose_name = '话题'
        verbose_name_plural = '话题列表'

    def __str__(self):
        return self.name


# 房间
class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='房间主持人')  # 房间主持人
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, verbose_name='房间话题')  # 房间话题
    name = models.CharField(max_length=200, verbose_name='房间名称')  # 房间名称
    description = models.TextField(null=True, blank=True, verbose_name='房间描述')  # 房间描述
    participants = models.ManyToManyField(User, related_name='participants', blank=True, verbose_name='参与者')  # 参与者
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')  # 创建时间
    updated = models.DateTimeField(auto_now=True, verbose_name='更新时间')  # 更新时间
    favorites = models.ManyToManyField(User, related_name='favorite_rooms', blank=True,
                                       verbose_name='收藏的房间')  # 收藏的房间
    encryption_key = models.CharField(max_length=255, blank=True, null=True, verbose_name='加密密钥')  # 加密密钥
    is_encrypted = models.BooleanField(default=False, verbose_name='是否加密')  # 标记房间是否加密
    is_hidden = models.BooleanField(default=False, verbose_name='是否隐藏')  # 新增字段，默认为 False

    class Meta:
        ordering = ['-updated', 'created']  # 按更新时间和创建时间排序
        verbose_name = '房间'
        verbose_name_plural = '房间列表'

    def __str__(self):
        return self.name

    def generate_encryption_key(self):
        self.encryption_key = Fernet.generate_key().decode()  # 生成新的加密密钥
        self.is_encrypted = True  # 设置加密状态为 True
        self.save()


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='发送用户')  # 发送消息的用户
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name='所在房间')  # 消息所在的房间
    body = models.TextField(verbose_name='消息内容')  # 消息内容
    image = models.ImageField(upload_to='images/', blank=True, null=True, verbose_name='附加图片')  # 附加图片
    video = models.FileField(upload_to='videos/', blank=True, null=True, verbose_name='附加视频')  # 附加视频
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')  # 创建时间
    updated = models.DateTimeField(auto_now=True, verbose_name='更新时间')  # 更新时间
    likes = models.ManyToManyField(User, related_name='liked_messages', blank=True, verbose_name='点赞用户')  # 点赞的用户
    encrypted_body = models.TextField(blank=True, null=True, verbose_name='加密消息内容')  # 存储加密后的消息内容

    class Meta:
        ordering = ['-updated', 'created']  # 按更新时间和创建时间排序
        verbose_name = '消息'
        verbose_name_plural = '消息列表'

    def __str__(self):
        return self.body[0:50]  # 返回消息前50个字符

    def encrypt_message(self, key):
        fernet = Fernet(key.encode())
        self.encrypted_body = fernet.encrypt(self.body.encode()).decode()

    def decrypt_message(self, key):
        fernet = Fernet(key.encode())
        return fernet.decrypt(self.encrypted_body.encode()).decode()


class Announcement(models.Model):
    title = models.CharField(max_length=200, verbose_name='公告标题')  # 公告标题
    content = models.TextField(verbose_name='公告内容')  # 公告内容
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='公告作者')  # 公告作者
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')  # 创建时间
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')  # 更新时间

    class Meta:
        verbose_name = '公告'
        verbose_name_plural = '公告列表'

    def __str__(self):
        return self.title  # 返回公告标题


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    message = models.CharField(max_length=255, verbose_name='通知内容')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='时间戳')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知列表'

    def __str__(self):
        return f"{self.user.username}: {self.message}"


# 好友列表
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    friends = models.ManyToManyField(User, related_name='friends_list', blank=True)

    def __str__(self):
        return self.user.username


class DirectMessageRoom(models.Model):
    user1 = models.ForeignKey(User, related_name='dm_room_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='dm_room_user2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user1.username} & {self.user2.username}"


class DirectMessage(models.Model):
    room = models.ForeignKey(DirectMessageRoom, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)  # 允许为空
    image = models.ImageField(upload_to='direct_messages/', blank=True, null=True)  # 新增图片字段
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content}"
