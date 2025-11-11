from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, HttpResponseRedirect
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.text import slugify
from django.contrib.admin.views.decorators import staff_member_required
from .models import Addon, Comment
from .forms import AddonForm, CommentForm
from django.utils.timezone import now
from datetime import timedelta
import re
from .models import BanRecord
from django.contrib.auth.decorators import login_required


class HomeView(TemplateView):
    """ホームページ"""
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_addons'] = Addon.objects.filter(published=True)[:6]
        context['addon_count'] = Addon.objects.filter(published=True).count()
        context['total_downloads'] = sum(a.downloads for a in Addon.objects.filter(published=True))
        return context


class AddonListView(ListView):
    """アドオン一覧"""
    model = Addon
    template_name = 'addon_list.html'
    context_object_name = 'addons'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Addon.objects.filter(published=True)
        
        # 検索
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(author__icontains=query) |
                Q(description__icontains=query)
            )
        
        # フィルタリング
        addon_type = self.request.GET.get('type')
        if addon_type:
            queryset = queryset.filter(addon_type=addon_type)
        
        # ソート
        sort_by = self.request.GET.get('sort', '-created_at')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['addon_types'] = Addon.ADDON_TYPE_CHOICES
        context['current_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class AddonDetailView(DetailView):
    """アドオン詳細"""
    model = Addon
    template_name = 'addon_detail.html'
    context_object_name = 'addon'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Addon.objects.filter(published=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['screenshots'] = self.object.screenshots.all()
        return context


def download_addon(request, slug):
    """アドオンをダウンロード"""
    addon = get_object_or_404(Addon, slug=slug, published=True)
    addon.increment_downloads()
    
    # ファイルをレスポンスとして返す
    file_handle = addon.download_file.open('rb')
    response = FileResponse(file_handle)
    # ファイル名がパスを含む可能性があるためbasenameを取得
    import os
    from urllib.parse import quote
    filename = os.path.basename(addon.download_file.name)
    # Set both filename (ascii fallback) and filename* (UTF-8) for modern browsers
    try:
        filename_ascii = filename.encode('ascii')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    except UnicodeEncodeError:
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    return response


class AddonCreateView(CreateView):
    """アドオンをアップロードするフォームビュー"""
    model = Addon
    form_class = AddonForm
    template_name = 'upload.html'

    def form_valid(self, form):
        # 自動で slug を生成（同名があれば連番を付ける）
        instance = form.save(commit=False)
        # 所有者を設定
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            instance.owner = self.request.user
        if not instance.slug:
            base = slugify(instance.name) or 'addon'
            slug = base
            counter = 1
            while Addon.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            instance.slug = slug
        instance.save()
        form.save_m2m()
        return HttpResponseRedirect(instance.get_absolute_url())


class AddonUpdateView(LoginRequiredMixin, UpdateView):
    """アドオンを編集（所有者のみ）"""
    model = Addon
    form_class = AddonForm
    template_name = 'upload.html'
    slug_field = 'slug'

    def get_queryset(self):
        # オーナー本人またはスタッフのみ編集可能
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(owner=self.request.user)

    def form_valid(self, form):
        instance = form.save(commit=False)
        # 所有者は変更させない
        if not instance.owner:
            instance.owner = self.request.user
        instance.save()
        form.save_m2m()
        messages.success(self.request, 'アドオン情報を更新しました。')
        return HttpResponseRedirect(instance.get_absolute_url())


@login_required
def post_comment(request, slug):
    addon = get_object_or_404(Addon, slug=slug, published=True)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.addon = addon
            comment.user = request.user
            comment.save()
    return redirect(addon.get_absolute_url())


@login_required
def publish_addon(request, slug):
    """オーナーまたはスタッフがアドオンを公開する（published=True にする）"""
    addon = get_object_or_404(Addon, slug=slug)
    # 権限チェック: オーナーかスタッフ
    if request.user != addon.owner and not request.user.is_staff:
        messages.error(request, '公開する権限がありません。')
        return redirect(addon.get_absolute_url())

    if request.method == 'POST':
        addon.published = True
        addon.save(update_fields=['published'])
        messages.success(request, 'アドオンを公開しました。')

    return redirect(addon.get_absolute_url())


@staff_member_required
def admin_command_console(request):
    """管理者専用: テキストコマンドを受け取り実行する小さなコンソール。

    サポートするコマンド例:
    /ban username [years,months,seconds]  -> 一時BAN。例: /ban foo 0,1,0 (0年1月0秒)
    /unban username                       -> BAN解除
    /banlist                              -> 現在のBAN一覧
    /kick username                        -> 一時的にキック（メッセージのみ）
    """
    output = []
    if request.method == 'POST':
        cmd = request.POST.get('command', '').strip()
        if cmd:
            output.append(f'> {cmd}')
            # /ban
            m = re.match(r'^/ban\s+(\S+)(?:\s+(\d+),(\d+),(\d+))?$', cmd)
            if m:
                username = m.group(1)
                years = int(m.group(2)) if m.group(2) else 0
                months = int(m.group(3)) if m.group(3) else 0
                seconds = int(m.group(4)) if m.group(4) else 0
                # convert years/months to days approx
                days = years * 365 + months * 30
                expires = None
                if days or seconds:
                    expires = now() + timedelta(days=days, seconds=seconds)
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    u = User.objects.get(username=username)
                    # create ban record
                    br = BanRecord.objects.create(user=u, banned_by=request.user, reason='admin console ban', expires_at=expires)
                    u.is_active = False
                    u.save(update_fields=['is_active'])
                    output.append(f'ユーザー {username} をBANしました。期限: {expires}')
                except User.DoesNotExist:
                    output.append(f'ユーザー {username} が見つかりません')
            elif cmd.startswith('/unban'):
                parts = cmd.split()
                if len(parts) >= 2:
                    username = parts[1]
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    try:
                        u = User.objects.get(username=username)
                        u.is_active = True
                        u.save(update_fields=['is_active'])
                        # mark current ban records expired
                        BanRecord.objects.filter(user=u, expires_at__isnull=True).update(expires_at=now())
                        output.append(f'ユーザー {username} のBANを解除しました')
                    except User.DoesNotExist:
                        output.append(f'ユーザー {username} が見つかりません')
                else:
                    output.append('使い方: /unban username')
            elif cmd.startswith('/banlist'):
                bans = BanRecord.objects.all()[:50]
                for b in bans:
                    output.append(f'{b.user.username} by {b.banned_by.username if b.banned_by else "system"} expires={b.expires_at}')
            elif cmd.startswith('/kick'):
                parts = cmd.split()
                if len(parts) >= 2:
                    username = parts[1]
                    output.append(f'ユーザー {username} をキックしました（実際の切断は未実装）')
                else:
                    output.append('使い方: /kick username')
            else:
                output.append('不明なコマンド')
    return render(request, 'admin/command_console.html', {'output': output})
