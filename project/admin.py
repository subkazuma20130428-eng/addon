from django.contrib import admin
from .models import Addon, AddonScreenshot


class AddonScreenshotInline(admin.TabularInline):
    model = AddonScreenshot
    extra = 1
    fields = ['image', 'caption', 'order']


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
    
    inlines = [AddonScreenshotInline]


@admin.register(AddonScreenshot)
class AddonScreenshotAdmin(admin.ModelAdmin):
    list_display = ['addon', 'caption', 'order']
    list_filter = ['addon']
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

    from .models import Inquiry

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    readonly_fields = ('name', 'email', 'message', 'created_at')

