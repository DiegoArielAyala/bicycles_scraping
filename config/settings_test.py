"""
Usage:
  python manage.py test apps.scraping.test.test_auth --settings=config.settings_test

"""

from config.settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "name": ":memory:",
    }
}

# Speed up User.objects.create_user / signup in tests (hashing is not under test).

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "scraping": {
            "handler": ["console"],
            "level": "DEBUG",
        }
    }
}