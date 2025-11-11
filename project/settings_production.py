import os
from pathlib import Path

# 本番環境用の設定（settings.py から分岐）
BASE_DIR = Path(__file__).resolve().parent.parent

# 本番環境では環境変数から SECRET_KEY を読む
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-key-change-in-production')

# 本番環境では DEBUG を False に
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS に本番ドメインを追加
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# 他の設定は settings.py から継承
from project.settings import *  # noqa

# 本番用の上書き設定
STATIC_ROOT = BASE_DIR / 'staticfiles'
