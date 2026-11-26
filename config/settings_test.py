"""
Usage:
  python manage.py test --settings=config.settings_test

"""

from config.settings import *  # noqa: F403

# Speed up User.objects.create_user / signup in tests (hashing is not under test).
POSTGRES_HOST_AUTH_METHOD="trust"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "memory",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    }
}
