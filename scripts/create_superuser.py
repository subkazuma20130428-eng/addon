import os
import sys
from pathlib import Path
# add repo root to PYTHONPATH so 'project' package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = 'masumc'
password = 'kazuma20130412@@'
if User.objects.filter(username=username).exists():
    print('already exists')
else:
    User.objects.create_superuser(username, '', password)
    print('created')
