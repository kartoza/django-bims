from celery import shared_task
from django.core.management import call_command

from bims.models.boundary_type import BoundaryType
from bims.models.boundary import Boundary


@shared_task(name='tasks.update_search_index')
def update_search_index():
    call_command('rebuild_index', '--noinput')


@shared_task(name='tasks.update_cluster')
def update_cluster(ids=None):
    if not ids:
        for boundary_type in BoundaryType.objects.all().order_by('-level'):
            for boundary in Boundary.objects.filter(type=boundary_type):
                print('generate cluster for %s' % boundary)
                boundary.generate_cluster()
    else:
        for boundary in Boundary.objects.filter(
                id__in=ids).order_by('-type__level'):
            print('generate cluster for %s' % boundary)
            boundary.generate_cluster()
