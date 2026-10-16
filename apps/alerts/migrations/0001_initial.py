import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("catalog", "0015_alter_pricehistory_bicycle_alter_bicycle_table_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Subscription",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("email", models.EmailField(max_length=120)),
                        (
                            "unsubscribe_token",
                            models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                        ),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        (
                            "bicycle",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.PROTECT,
                                related_name="subscriptions",
                                to="catalog.bicycle",
                            ),
                        ),
                        (
                            "user",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.PROTECT,
                                related_name="subscriptions",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        "db_table": "scraping_subscription",
                        "indexes": [
                            models.Index(
                                fields=["created_at"], name="scraping_su_created_d3fd50_idx"
                            )
                        ],
                        "constraints": [
                            models.UniqueConstraint(
                                fields=("user", "bicycle"),
                                name="unique_user_bicycle_subscription",
                            )
                        ],
                    },
                ),
            ],
        ),
    ]
