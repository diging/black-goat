from __future__ import absolute_import

from django.conf import settings
from celery import Celery
import os, sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goat.settings')

app = Celery('goat')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.update(BROKER_URL=os.environ.get('REDISTOGO_URL', 'redis://localhost:6379/0'),
                CELERY_DEFAULT_QUEUE = 'goat',
                CELERY_RESULT_BACKEND=os.environ.get('REDISTOGO_URL', 'redis://localhost:6379/0'))
app.conf.task_default_queue = 'goat'
app.conf.task_routes = {'goat.tasks.*': {'queue': 'goat'}}
