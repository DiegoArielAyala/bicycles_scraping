from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0014_alter_bicycle_last_seen_at"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="Subscription"),
            ],
        ),
    ]
