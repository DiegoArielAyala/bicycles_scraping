import django
import os

from apps.accounts.permissions import ROLE_ADMIN

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", os.getenv("HOTMAIL"))
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", os.getenv("SU_PASSWORD"))

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser {username}")
    user = User.objects.create_superuser(username=username, email=email, password=password)

    group = Group.objects.get(name=ROLE_ADMIN)

    user.groups.add(group)
else:
    print(f"Superuser {username} already exists")