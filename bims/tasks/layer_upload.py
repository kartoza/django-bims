# coding=utf-8
"""Cloud Native GIS."""
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(name='bims.tasks.import_layer_data', queue='update', ignore_result=True)
def import_layer_data(layer_id):
    """Import data from layer id."""
    from cloud_native_gis.models import LayerUpload
    try:
        layer = LayerUpload.objects.get(id=layer_id)
        layer.import_data()
    except LayerUpload.DoesNotExist:
        logger.error(f'Layer {layer_id} does not exist')
