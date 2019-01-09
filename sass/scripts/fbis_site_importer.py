from django.db.models import signals
from django.db.utils import DataError
from django.contrib.gis.geos import Point
from easyaudit.signals.model_signals import pre_save as easyaudit_presave
from bims.models import (
    FbisUUID,
    LocationSite,
    LocationType,
    location_site_post_save_handler
)
from sass.scripts.fbis_importer import FbisImporter


class FbisSiteImporter(FbisImporter):

    content_type_model = LocationSite
    table_name = 'Site'

    def __init__(self, sqlite_filename, max_row=None):
        super(FbisSiteImporter, self).__init__(sqlite_filename, max_row)
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

        # Get river
        river = None
        river_uuid = self.get_row_value('RiverID', row)
        if river_uuid:
            rivers = FbisUUID.objects.filter(
                uuid=river_uuid
            )
            if rivers.exists():
                river = rivers[0].content_object

        lon = self.get_row_value('LongitudeGIS', row)
        lat = self.get_row_value('LatitudeGIS', row)
        try:
            record_point = Point(float(lon), float(lat))
        except ValueError as e:
            print(e.message)
            return

        try:
            location_site, created = LocationSite.objects.get_or_create(
                name=self.get_row_value('Site', row),
                site_code=self.get_row_value('SiteCode', row),
                latitude=lat,
                longitude=lon,
                river=river,
                geometry_point=record_point,
                location_type=self.location_type
            )
        except DataError as e:
            print(e)
            return

        location_site.map_reference = self.get_row_value('MapReference', row)
        location_site.site_description = self.get_row_value(
            'CommentSiteGeneral',
            row
        )
        location_site.land_owner_detail = self.get_row_value(
            'LandOwnerDetail',
            row
        )
        location_site.additional_data = {
            'Farm': self.get_row_value('Farm', row),
            'OldSiteCode': self.get_row_value('OldSiteCode', row),
            'Source': self.get_row_value('Source', row),
            'UserID': self.get_row_value('UserID', row)
        }
        location_site.save()
        self.save_uuid(
            uuid=self.get_row_value('SiteID', row),
            object_id=location_site.id
        )
