from django.db.models import signals
from django.db.utils import DataError
from django.contrib.gis.geos import Point
from django.contrib.contenttypes.models import ContentType
from easyaudit.signals.model_signals import pre_save as easyaudit_presave
from geonode.people.models import Profile
from sass.scripts.fbis_postgres_importer import FbisPostgresImporter
from sass.models.river import River
from bims.models import (
    FbisUUID,
    LocationSite,
    LocationType,
    location_site_post_save_handler
)


class FbisBiobaseSiteImporter(FbisPostgresImporter):

    table_name = 'public."BioSite"'
    content_type_model = LocationSite

    def __init__(self, sqlite_filename, max_row=None):
        super(FbisBiobaseSiteImporter, self).__init__(sqlite_filename, max_row)
        self.location_type, created = LocationType.objects.get_or_create(
            name='RiverPointObservation',
            description='Imported from fbis database',
            allowed_geometry='POINT'
        )

    def start_processing_rows(self):
        signals.post_save.disconnect(
            location_site_post_save_handler,
        )
        signals.pre_save.disconnect(
            easyaudit_presave,
            dispatch_uid='easy_audit_signals_pre_save'
        )

    def finish_processing_rows(self):
        signals.post_save.connect(
            location_site_post_save_handler,
        )

    def process_row(self, row, index):
        lon = self.get_row_value('LongitudeGIS')
        lat = self.get_row_value('LatitudeGIS')
        try:
            record_point = Point(float(lon), float(lat))
        except ValueError as e:
            print(e.message)
            return

        river = None
        river_name = self.get_row_value('RiverName')
        if river_name:
            river, river_created = River.objects.get_or_create(
                name=river_name
            )
            river.additional_data = {
                'UserID': self.get_row_value('User'),
                'BioBaseData': True
            }
            river.save()
            FbisUUID.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(
                    River
                ),
                object_id=river.id,
                uuid=self.get_row_value('BioRiverNameID')
            )

        try:
            location_site, created = LocationSite.objects.get_or_create(
                name=self.get_row_value('SiteCode'),
                site_code=self.get_row_value('SiteCode'),
                latitude=lat,
                longitude=lon,
                geometry_point=record_point,
                location_type=self.location_type
            )
        except DataError as e:
            print(e)
            return
        location_site.site_description = self.get_row_value(
            'Description',
            row
        )
        location_site.additional_data = {
            'OldSiteCode': self.get_row_value('SiteCode'),
            'UserID': self.get_row_value('User'),
            'BioBaseData': True
        }

        if river:
            location_site.river = river

        # Get user if exist
        user_ctype = ContentType.objects.get_for_model(
            Profile
        )
        owner = None
        owners = FbisUUID.objects.filter(
            uuid=self.get_row_value('User'),
            content_type=user_ctype
        )
        if owners.exists():
            owner = owners[0].content_object
        if owner:
            location_site.owner = owner

        location_site.save()
        self.save_uuid(
            uuid=self.get_row_value('BioSiteID'),
            object_id=location_site.id
        )
