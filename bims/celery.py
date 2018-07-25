from __future__ import absolute_import

from celery import Celery

app = Celery('bims')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(['bims',])

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
