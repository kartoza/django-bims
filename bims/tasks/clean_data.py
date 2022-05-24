import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.clean_data', queue='update')
def clean_data():
    from bims.models.water_temperature import WaterTemperature

    water_temperatures_without_site = (
        WaterTemperature.objects.filter(
            location_site__isnull=True
        )
    )

    if water_temperatures_without_site.exists():
        logger.debug('Found {} water_temperature without site'.format(
            water_temperatures_without_site.count()
        ))
        water_temperatures_without_site.delete()
