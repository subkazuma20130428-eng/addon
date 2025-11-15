from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, HttpResponseRedirect
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import ProgrammingError, OperationalError
from django.utils.text import slugify
from django.contrib.admin.views.decorators import staff_member_required
from .models import Addon, Comment, ContactMessage
from .forms import AddonForm, CommentForm
from .forms import ContactForm, ReportForm, WikiForm
from .models import TermsPage, Report, Announcement, Wiki
from django.core.mail import send_mail
from django.conf import settings
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
        # DB テーブルが未作成（マイグレーション未実行）などでエラーになると 500 になるため
        # 一時的に例外を握りつぶして空のデータでフォールバックする。
        try:
            context['latest_addons'] = Addon.objects.filter(published=True)[:6]
            context['addon_count'] = Addon.objects.filter(published=True).count()
            context['total_downloads'] = sum(a.downloads for a in Addon.objects.filter(published=True))
        except (ProgrammingError, OperationalError):
            # 本番DBにテーブルがない等の初期化前の状態向けフォールバック
            context['latest_addons'] = []
            context['addon_count'] = 0
            context['total_downloads'] = 0
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
        addon = self.object
        user = self.request.user

        # スクリーンショット一覧
        context['screenshots'] = addon.screenshots.all()

        # ログインしているかチェックして安全に処理
        context['is_owner'] = user.is_authenticated and addon.owner == user
        # Provide both names so templates using either 'form' or 'comment_form' work
        context['comment_form'] = CommentForm()
        context['form'] = context['comment_form']
        context['comments'] = Comment.objects.filter(addon=addon).order_by('-created_at')

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
            messages.success(request, 'コメントを投稿しました。')
        else:
            # Inform user about validation errors
            messages.error(request, 'コメントを投稿できませんでした。入力内容を確認してください。')
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


def contact_view(request):
    """問い合わせページ。フォーム送信をDBの `ContactMessage` に保存し、管理画面で確認できるようにする。"""
    from .models import ContactMessage

    if request.method == 'POST':
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data.get('subject') or ''
            message = form.cleaned_data['message']
            image = request.FILES.get('image')

            # DBに保存
            contact = ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            if image:
                contact.image = image
                contact.save()

            messages.success(request, 'お問い合わせを受け付けました。管理者が確認します。')
            return redirect('contact')
    else:
        form = ContactForm()
    # 管理者向けに最近の問い合わせ一覧も渡す
    contact_list = None
    if request.user.is_staff:
        contact_list = ContactMessage.objects.all().order_by('-created_at')[:200]
    else:
        # ログインユーザーは自分が送った問い合わせ（メール一致）を表示
        if request.user.is_authenticated:
            contact_list = ContactMessage.objects.filter(email=request.user.email).order_by('-created_at')[:50]

    return render(request, 'contact.html', {'form': form, 'contact_list': contact_list})


@staff_member_required
def contact_toggle_handled(request, pk):
    """管理者が問い合わせの handled フラグを切り替えるための簡易ビュー（POST）。"""
    from django.shortcuts import get_object_or_404
    if request.method == 'POST':
        cm = get_object_or_404(ContactMessage, pk=pk)
        cm.handled = not cm.handled
        if cm.handled:
            cm.handled_by = request.user
        else:
            cm.handled_by = None
        cm.save(update_fields=['handled', 'handled_by'])
    return redirect('contact')


@staff_member_required
def contact_reply(request, pk):
    """管理者が問い合わせに対して返信メールを送信するビュー。

    POST パラメータ:
      - reply_subject (任意)
      - reply_message (必須)
    送信元は settings.DEFAULT_FROM_EMAIL を使い、送信先は問い合わせのメールアドレス。
    送信成功時は問い合わせを対応済みにして handled_by を設定する。
    """
    from django.shortcuts import get_object_or_404
    if request.method != 'POST':
        return redirect('contact')

    cm = get_object_or_404(ContactMessage, pk=pk)
    reply_subject = request.POST.get('reply_subject') or f'お問い合わせへの返信: {cm.subject or "(件名なし)"}'
    reply_message = request.POST.get('reply_message', '').strip()
    if not reply_message:
        messages.error(request, '返信メッセージを入力してください。')
        return redirect('contact')

    # 送信元アドレス
    from_addr = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or cm.email

    try:
        send_mail(reply_subject, reply_message, from_addr, [cm.email], fail_silently=False)
        # マーク対応済み
        cm.handled = True
        cm.handled_by = request.user
        cm.save(update_fields=['handled', 'handled_by'])
        # DBに返信を保存
        from .models import ContactReply
        ContactReply.objects.create(
            contact=cm,
            subject=reply_subject,
            message=reply_message,
            replied_by=request.user
        )
        messages.success(request, f'返信を送信しました: {cm.email}')
    except Exception as e:
        messages.error(request, f'返信の送信に失敗しました: {e}')

    return redirect('contact')


def terms_view(request):
    """利用規約ページ。管理画面で編集した最新の active=True ページを表示する。"""
    page = TermsPage.objects.filter(active=True).order_by('-created_at').first()
    if not page:
        # デフォルト文言
        page = TermsPage(title='利用規約', content='利用規約はまだ設定されていません。管理画面で追加してください。', active=True)
    return render(request, 'terms.html', {'page': page})


def announcement_view(request):
    """お知らせ一覧ページ。公開中のお知らせを新着順で表示する。"""
    announcements = Announcement.objects.filter(published=True).order_by('-created_at')
    return render(request, 'announcement.html', {'announcements': announcements})


@login_required
def report_view(request):
    """通報ページ。ログインユーザーは reporter に自動設定される。"""
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            if request.user.is_authenticated:
                report.reporter = request.user
            report.save()
            messages.success(request, '通報を受け付けました。管理者が確認します。')
            return redirect('report')
    else:
        form = ReportForm()
    return render(request, 'report.html', {'form': form})


class WikiListView(ListView):
    """Wiki ページ一覧"""
    model = Wiki
    template_name = 'wiki_list.html'
    context_object_name = 'wikis'
    paginate_by = 20

    def get_queryset(self):
        queryset = Wiki.objects.all()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class WikiDetailView(DetailView):
    """Wiki ページ詳細表示"""
    model = Wiki
    template_name = 'wiki_detail.html'
    context_object_name = 'wiki'
    slug_field = 'slug'


class WikiCreateView(LoginRequiredMixin, CreateView):
    """Wiki ページ作成"""
    model = Wiki
    form_class = WikiForm
    template_name = 'wiki_form.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.created_by = self.request.user
        instance.updated_by = self.request.user
        # slug が空なら title から自動生成
        if not instance.slug:
            base = slugify(instance.title) or 'wiki'
            slug = base
            counter = 1
            while Wiki.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            instance.slug = slug
        instance.save()
        messages.success(self.request, 'Wiki ページを作成しました。')
        return super().form_valid(form)


class WikiUpdateView(LoginRequiredMixin, UpdateView):
    """Wiki ページ編集（全ユーザー可能）"""
    model = Wiki
    form_class = WikiForm
    template_name = 'wiki_form.html'
    slug_field = 'slug'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.updated_by = self.request.user
        instance.save()
        messages.success(self.request, 'Wiki ページを更新しました。')
        return super().form_valid(form)
