"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    HomeView,
    AddonListView,
    AddonDetailView,
    download_addon,
    publish_addon,
    AddonCreateView,
    AddonUpdateView,
    admin_command_console,
    post_comment,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # ホームページ
    path('', HomeView.as_view(), name='home'),
    # アドオン関連
    path('addons/', AddonListView.as_view(), name='addon_list'),
    path('addons/<slug:slug>/', AddonDetailView.as_view(), name='addon_detail'),
    path('addons/<slug:slug>/download/', download_addon, name='download_addon'),
    path('addons/<slug:slug>/publish/', publish_addon, name='publish_addon'),
    # アップロードフォーム
    path('upload/', AddonCreateView.as_view(), name='addon_upload'),
    path('upload/<slug:slug>/edit/', AddonUpdateView.as_view(), name='addon_edit'),
    path('addons/<slug:slug>/comment/', post_comment, name='post_comment'),
    path('accounts/', include('allauth.urls')),
    # 管理者用コマンドコンソール
    path('admin/commands/', admin_command_console, name='admin_command_console'),
]

# メディアファイルの配信（開発環境用）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
