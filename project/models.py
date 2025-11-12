from django.db import models
from django.utils.timezone import now
from django.urls import reverse
from django.db import models


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

# app/models.py

class TermsOfService(models.Model):
    """利用規約ページ"""
    title = models.CharField(max_length=200, default="利用規約")
    content = models.TextField(help_text="利用規約の本文を入力してください。")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ContactPage(models.Model):
    """お問い合わせページ（説明文など）"""
    title = models.CharField(max_length=200, default="お問い合わせ")
    content = models.TextField(help_text="お問い合わせページに表示する文章（例: メールでのお問い合わせ先など）")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
