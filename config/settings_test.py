"""
Usage:
  python manage.py test --settings=config.settings_test

"""

from config.settings import *  # noqa: F403

# Speed up User.objects.create_user / signup in tests (hashing is not under test).

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "bike_test",
        "USER": "bike_test",
        "PASSWORD": "password_test",
        "HOST": '127.0.0.1',
        "PORT": '5432',
    },
}

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
            "handlers": ["console"],
            "level": "DEBUG",
        }
    }
}