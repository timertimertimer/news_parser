import os
from celery import Celery
from celery.schedules import timedelta


os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'news_parser.settings')

app = Celery('news_parser')
app.config_from_object('django.conf:settings', namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'habr': {
        'task': 'main.tasks.parse_habr',
        'schedule': timedelta(minutes=3),
    },
    'iz': {
        'task': 'main.tasks.parse_iz',
        'schedule': timedelta(minutes=3),
    },
    'mk': {
        'task': 'main.tasks.parse_mk',
        'schedule': timedelta(minutes=3),
    },
    'rbk': {
        'task': 'main.tasks.parse_rbk',
        'schedule': timedelta(minutes=3),
    },
    'tass': {
        'task': 'main.tasks.parse_tass',
        'schedule': timedelta(minutes=3),
    },
}
