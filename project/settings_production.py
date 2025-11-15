import os
from pathlib import Path

# 本番環境用の設定（settings.py から分岐）
BASE_DIR = Path(__file__).resolve().parent.parent

# 他の設定は settings.py から継承
from project.settings import *  # noqa

# 本番環境では環境変数から SECRET_KEY を読む
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-key-change-in-production')

# 本番環境では DEBUG を False に
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS に本番ドメインを追加（環境変数がない場合はレンダリング用ホストを設定）
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,mainkurahutoadoonzu.onrender.com').split(',')

# 本番用の上書き設定
STATIC_ROOT = BASE_DIR / 'staticfiles'

# セッションセキュリティ設定（本番環境用）
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Renderにおけるプロトコル設定
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
