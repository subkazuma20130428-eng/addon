from django.contrib import admin
from .models import Addon, AddonScreenshot, AddonVideo


class AddonScreenshotInline(admin.TabularInline):
    model = AddonScreenshot
    extra = 1
    fields = ['image', 'caption', 'order']


class AddonVideoInline(admin.TabularInline):
    model = AddonVideo
    extra = 1
    fields = ['video_type', 'video_file', 'video_url', 'thumbnail', 'caption', 'order']


@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ['name', 'addon_type', 'version', 'author', 'owner', 'downloads', 'published', 'created_at']
    list_filter = ['addon_type', 'published', 'created_at']
    search_fields = ['name', 'author', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['downloads', 'likes', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'slug', 'addon_type', 'author')
        }),
        ('説明', {
            'fields': ('description', 'long_description')
        }),
        ('バージョン情報', {
            'fields': ('version', 'minecraft_version')
        }),
        ('メディア', {
            'fields': ('thumbnail', 'download_file')
        }),
        ('統計', {
            'fields': ('downloads', 'likes'),
            'classes': ('collapse',)
        }),
        ('公開設定', {
            'fields': ('published', 'created_at', 'updated_at')
        }),
    )
    
    inlines = [AddonScreenshotInline, AddonVideoInline]


@admin.register(AddonScreenshot)
class AddonScreenshotAdmin(admin.ModelAdmin):
    list_display = ['addon', 'caption', 'order']
    list_filter = ['addon']
    search_fields = ['addon__name', 'caption']
    ordering = ['addon', 'order']


@admin.register(AddonVideo)
class AddonVideoAdmin(admin.ModelAdmin):
    list_display = ['addon', 'video_type', 'caption', 'order']
    list_filter = ['addon', 'video_type']
    search_fields = ['addon__name', 'caption']
    ordering = ['addon', 'order']


from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['addon', 'user', 'created_at']
    search_fields = ['addon__name', 'user__username', 'text']
    list_filter = ['created_at']


# --- Admin actions for banning/unbanning users ---
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

User = get_user_model()


@admin.action(description='選択したユーザーをBAN（無効化）する')
def ban_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f'{updated} 件のユーザーをBAN（無効化）しました。')


@admin.action(description='選択したユーザーを解除（有効化）する')
def unban_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f'{updated} 件のユーザーを有効化しました。')


class CustomUserAdmin(DjangoUserAdmin):
    actions = [ban_users, unban_users] + list(getattr(DjangoUserAdmin, 'actions', []) or [])


try:
    admin.site.unregister(User)
except Exception:
    pass
admin.site.register(User, CustomUserAdmin)

# Register BanRecord in admin
from .models import BanRecord


@admin.register(BanRecord)
class BanRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'banned_by', 'reason', 'created_at', 'expires_at']
    search_fields = ['user__username', 'banned_by__username', 'reason']
    list_filter = ['created_at']


from .models import TermsPage, Report


@admin.register(TermsPage)
class TermsPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'active', 'created_at', 'updated_at']
    list_filter = ['active', 'created_at']
    search_fields = ['title', 'content']
    fieldsets = (
        ('基本情報', {
            'fields': ('title', 'active')
        }),
        ('内容', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('メタデータ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        """新規作成時は自動で active=True にし、編集時は active=True を選択したら他の同一タイトルのページを inactive にする"""
        if not change:
            obj.active = True
        super().save_model(request, obj, form, change)
        # 同一タイトルで active=True の他のページを inactive にする
        if obj.active:
            TermsPage.objects.filter(title=obj.title).exclude(pk=obj.pk).update(active=False)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'addon', 'created_at', 'resolved']
    list_filter = ['resolved', 'created_at']
    search_fields = ['reporter__username', 'addon__name', 'description']
    actions = ['mark_resolved']

    @admin.action(description='選択した通報を対応済みにする')
    def mark_resolved(self, request, queryset):
        updated = queryset.update(resolved=True, handled_by=request.user)
        self.message_user(request, f'{updated} 件の通報を対応済みにしました')


# Register ContactMessage in admin (問い合わせを通報ページ風に管理できるように)
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'handled']
    list_filter = ['handled', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at']
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'email')
        }),
        ('メッセージ', {
            'fields': ('subject', 'message'),
            'classes': ('wide',)
        }),
        ('添付ファイル', {
            'fields': ('image',)
        }),
        ('対応状況', {
            'fields': ('handled', 'handled_by')
        }),
        ('メタデータ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_handled']

    @admin.action(description='選択した問い合わせを対応済みにする')
    def mark_handled(self, request, queryset):
        updated = queryset.update(handled=True, handled_by=request.user)
        self.message_user(request, f'{updated} 件の問い合わせを対応済みにしました')


from .models import ContactReply


@admin.register(ContactReply)
class ContactReplyAdmin(admin.ModelAdmin):
    list_display = ['contact', 'replied_by', 'replied_at']
    search_fields = ['contact__name', 'contact__email', 'message']
    list_filter = ['replied_at']


from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'published', 'created_at', 'updated_at']
    list_filter = ['published', 'created_at']
    search_fields = ['title', 'content']
    fieldsets = (
        ('基本情報', {
            'fields': ('title', 'published')
        }),
        ('内容', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('メディア', {
            'fields': ('image', 'video_url')
        }),
        ('メタデータ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


from .models import Wiki


@admin.register(Wiki)
class WikiAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'updated_by', 'created_at', 'updated_at']
    search_fields = ['title', 'content']
    list_filter = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']
    fieldsets = (
        ('基本情報', {
            'fields': ('title', 'slug')
        }),
        ('内容', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('メディア', {
            'fields': ('image', 'video_url')
        }),
        ('ユーザー情報', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    fieldsets = (
        ('基本情報', {
            'fields': ('title', 'slug')
        }),
        ('内容', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('メタデータ', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
