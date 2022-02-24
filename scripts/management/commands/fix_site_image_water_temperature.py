from django.core.management import BaseCommand
from bims.models.water_temperature import WaterTemperature
from bims.models.site_image import SiteImage, WATER_TEMPERATURE_KEY


class Command(BaseCommand):
    # Merge duplicated sites

    def handle(self, *args, **options):
        site_images = SiteImage.objects.filter(
            form_uploader=WATER_TEMPERATURE_KEY,
            owner__isnull=True
        )
        for site_image in site_images:
            water_temperature = WaterTemperature.objects.filter(
                location_site=site_image.site
            )
            if water_temperature.exists():
                wt = water_temperature.first()
                site_image.uploader = wt.uploader
                site_image.owner = wt.owner
                site_image.save()
