from __future__ import absolute_import

from tenant_schemas_celery.app import CeleryApp as TenantAwareCeleryApp

app = TenantAwareCeleryApp()

app.config_from_object('django.conf:settings', namespace="CELERY")
app.conf.update(
    task_default_queue='update',
)
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
