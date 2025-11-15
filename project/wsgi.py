import os
from django.core.wsgi import get_wsgi_application

# 本番環境（Renderなど）では DJANGO_SETTINGS_MODULE を settings_production に設定
# ローカル開発では settings に設定
if os.environ.get('ENVIRONMENT') == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings_production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

application = get_wsgi_application()
