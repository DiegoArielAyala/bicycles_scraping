from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
import os

User = get_user_model()

if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser(
        username="admin",
        email=os.getenv("HOTMAIL"),
        password=os.getenv("DB_PASSWORD")
    )
    print("Superuser creado")
else:
    print("Superuser ya existe")
