from django.db import models
from django.utils.timezone import now
from django.urls import reverse


class Addon(models.Model):
    """Minecraft Addon (Behavior Pack / Resource Pack)"""
    ADDON_TYPE_CHOICES = [
        ('behavior', 'ビヘイビアパック'),
        ('resource', 'リソースパック'),
        ('skin', 'スキンパック'),
        ('world', 'ワールドテンプレート'),
        ('other', 'その他'),
    ]

    name = models.CharField('アドオン名', max_length=100)
    slug = models.SlugField('URL用の名前', unique=True)
    description = models.TextField('説明')
    long_description = models.TextField('詳細説明', blank=True)
    addon_type = models.CharField('種類', max_length=20, choices=ADDON_TYPE_CHOICES, default='behavior')
    
    version = models.CharField('バージョン', max_length=20)
    author = models.CharField('作成者', max_length=100)
    
    minecraft_version = models.CharField('対応 Minecraft バージョン', max_length=50, default='1.21+')
    
    # メディア
    thumbnail = models.ImageField('サムネイル', upload_to='addons/thumbnails/', null=True, blank=True)
    download_file = models.FileField('ダウンロードファイル', upload_to='addons/files/')
    
    # メタデータ
    downloads = models.IntegerField('ダウンロード数', default=0)
    likes = models.IntegerField('いいね数', default=0)
    created_at = models.DateTimeField('作成日', auto_now_add=True)
    updated_at = models.DateTimeField('更新日', auto_now=True)
    published = models.BooleanField('公開', default=True)
    # 所有者（アップロードしたユーザー）。公開環境ではログイン必須にして設定します。
    from django.conf import settings
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='作成者ユーザー', null=True, blank=True, on_delete=models.SET_NULL, related_name='addons')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'アドオン'
        verbose_name_plural = 'アドオン'

    def __str__(self):
        return f'{self.name} ({self.get_addon_type_display()})'

    def get_absolute_url(self):
        return reverse('addon_detail', kwargs={'slug': self.slug})

    def increment_downloads(self):
        self.downloads += 1
        self.save(update_fields=['downloads'])


class AddonScreenshot(models.Model):
    """Screenshots for addon detail page"""
    addon = models.ForeignKey(Addon, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField('スクリーンショット', upload_to='addons/screenshots/')
    caption = models.CharField('キャプション', max_length=255, blank=True)
    order = models.PositiveIntegerField('順序', default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'スクリーンショット'
        verbose_name_plural = 'スクリーンショット'

    def __str__(self):
        return f'{self.addon.name} - Screenshot {self.order}'


class AddonVideo(models.Model):
    """動画（アップロード＆URL両対応）"""
    VIDEO_TYPE_CHOICES = [
        ('file', 'ファイルアップロード'),
        ('youtube', 'YouTube URL'),
        ('other', 'その他URL'),
    ]
    
    addon = models.ForeignKey(Addon, on_delete=models.CASCADE, related_name='videos')
    video_type = models.CharField('動画タイプ', max_length=20, choices=VIDEO_TYPE_CHOICES, default='file')
    video_file = models.FileField('動画ファイル', upload_to='addons/videos/', null=True, blank=True)
    video_url = models.URLField('動画URL（YouTubeなど）', null=True, blank=True)
    caption = models.CharField('キャプション', max_length=255, blank=True)
    thumbnail = models.ImageField('サムネイル', upload_to='addons/video_thumbnails/', null=True, blank=True)
    order = models.PositiveIntegerField('順序', default=0)
    created_at = models.DateTimeField('作成日', auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = '動画'
        verbose_name_plural = '動画'

    def __str__(self):
        return f'{self.addon.name} - Video {self.order}'

    def get_embed_url(self):
        """YouTubeのURLを埋め込み対応のURLに変換"""
        if self.video_type == 'youtube' and self.video_url:
            # https://www.youtube.com/watch?v=xxxxx → https://www.youtube.com/embed/xxxxx
            if 'watch?v=' in self.video_url:
                video_id = self.video_url.split('watch?v=')[1].split('&')[0]
                return f'https://www.youtube.com/embed/{video_id}'
            elif 'youtu.be/' in self.video_url:
                video_id = self.video_url.split('youtu.be/')[1].split('?')[0]
                return f'https://www.youtube.com/embed/{video_id}'
        return self.video_url


class Comment(models.Model):
    addon = models.ForeignKey(Addon, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField('コメント')
    created_at = models.DateTimeField('作成日', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'コメント'
        verbose_name_plural = 'コメント'

    def __str__(self):
        user = self.user.username if self.user else '匿名'
        return f'{self.addon.name} - {user}: {self.text[:30]}'


class TermsPage(models.Model):
    """サイト内で表示する利用規約や固定ページを管理するモデル。管理画面で編集可能にする。"""
    title = models.CharField('タイトル', max_length=200, default='利用規約')
    content = models.TextField('本文')
    active = models.BooleanField('公開中', default=True, help_text='有効なページが複数ある場合は最新の active=True を表示します')
    created_at = models.DateTimeField('作成日', auto_now_add=True)
    updated_at = models.DateTimeField('更新日', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '利用規約設定'
        verbose_name_plural = '利用規約設定'

    def __str__(self):
        return self.title


class Announcement(models.Model):
    """お知らせを管理するモデル。管理画面で追加・編集・削除可能。"""
    title = models.CharField('タイトル', max_length=200)
    content = models.TextField('内容')
    image = models.ImageField('画像', upload_to='announcements/', null=True, blank=True)
    video_url = models.URLField('動画URL（YouTubeなど）', null=True, blank=True)
    published = models.BooleanField('公開', default=True)
    created_at = models.DateTimeField('作成日', auto_now_add=True)
    updated_at = models.DateTimeField('更新日', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'お知らせ'
        verbose_name_plural = 'お知らせ'

    def __str__(self):
        return self.title

    def get_embed_url(self):
        """YouTubeのURLを埋め込み対応のURLに変換"""
        if self.video_url:
            # https://www.youtube.com/watch?v=xxxxx → https://www.youtube.com/embed/xxxxx
            if 'watch?v=' in self.video_url:
                video_id = self.video_url.split('watch?v=')[1].split('&')[0]
                return f'https://www.youtube.com/embed/{video_id}'
            elif 'youtu.be/' in self.video_url:
                video_id = self.video_url.split('youtu.be/')[1].split('?')[0]
                return f'https://www.youtube.com/embed/{video_id}'
        return self.video_url


class Wiki(models.Model):
    """Wiki ページを管理するモデル。ユーザーが自由に作成・編集可能。"""
    title = models.CharField('タイトル', max_length=200, unique=True)
    slug = models.SlugField('URL用の名前', unique=True)
    image = models.ImageField('サムネイル画像', upload_to='wiki/', null=True, blank=True)
    video_url = models.URLField('動画URL（YouTubeなど）', null=True, blank=True)
    content = models.TextField('内容')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='wiki_created')
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='wiki_updated')
    created_at = models.DateTimeField('作成日', auto_now_add=True)
    updated_at = models.DateTimeField('更新日', auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Wiki ページ'
        verbose_name_plural = 'Wiki ページ'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('wiki_detail', kwargs={'slug': self.slug})

    def get_embed_url(self):
        """YouTubeのURLを埋め込み対応のURLに変換"""
        if self.video_url:
            # https://www.youtube.com/watch?v=xxxxx → https://www.youtube.com/embed/xxxxx
            if 'watch?v=' in self.video_url:
                video_id = self.video_url.split('watch?v=')[1].split('&')[0]
                return f'https://www.youtube.com/embed/{video_id}'
            elif 'youtu.be/' in self.video_url:
                video_id = self.video_url.split('youtu.be/')[1].split('?')[0]
                return f'https://www.youtube.com/embed/{video_id}'
        return self.video_url


class Report(models.Model):
    """ユーザーからの通報を保存するモデル。通報対象 (addon) は任意。"""
    reporter = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    addon = models.ForeignKey(Addon, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    url = models.URLField('通報対象のURL', blank=True)
    description = models.TextField('通報内容')
    created_at = models.DateTimeField('作成日', auto_now_add=True)
    resolved = models.BooleanField('対応済み', default=False)
    handled_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_reports')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '通報'
        verbose_name_plural = '通報'

    def __str__(self):
        who = self.reporter.username if self.reporter else '匿名'
        target = self.addon.name if self.addon else (self.url or '指定なし')
        return f'{who} -> {target} ({self.created_at:%Y-%m-%d})'


class BanRecord(models.Model):
    """管理者が作成するBANレコード。ユーザーの一時停止/永久停止を記録する。"""
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='ban_records')
    banned_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='bans_issued')
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text='NULL=永久BAN')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'BAN履歴'
        verbose_name_plural = 'BAN履歴'

    def __str__(self):
        return f'BAN: {self.user.username} by {self.banned_by.username if self.banned_by else "system"}'

    @property
    def is_active(self):
        from django.utils.timezone import now
        if self.expires_at is None:
            return True
        return now() < self.expires_at


class ContactMessage(models.Model):
    """お問い合わせ（フォーム送信内容）をDBに保存するモデル。管理画面で確認・対応する想定。"""
    name = models.CharField('お名前', max_length=200)
    email = models.EmailField('メールアドレス')
    subject = models.CharField('件名', max_length=200, blank=True)
    message = models.TextField('メッセージ')
    image = models.ImageField('画像添付', upload_to='contact_images/', null=True, blank=True)
    created_at = models.DateTimeField('作成日', auto_now_add=True)
    handled = models.BooleanField('対応済み', default=False)
    handled_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_contacts')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'お問い合わせメッセージ'
        verbose_name_plural = 'お問い合わせメッセージ'

    def __str__(self):
        return f'{self.name} <{self.email}> - {self.subject or "(件名なし)"} ({self.created_at:%Y-%m-%d %H:%M})'


class ContactReply(models.Model):
    """管理者からの返信を保存するモデル。1つの問い合わせに対して複数返信を残せる。"""
    contact = models.ForeignKey(ContactMessage, on_delete=models.CASCADE, related_name='replies')
    subject = models.CharField('件名', max_length=200, blank=True)
    message = models.TextField('メッセージ')
    replied_at = models.DateTimeField('返信日時', auto_now_add=True)
    replied_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_replies')

    class Meta:
        ordering = ['-replied_at']
        verbose_name = '問い合わせ返信'
        verbose_name_plural = '問い合わせ返信'

    def __str__(self):
        return f'Reply to {self.contact.id} by {self.replied_by.username if self.replied_by else "(unknown)"} at {self.replied_at:%Y-%m-%d %H:%M}'
