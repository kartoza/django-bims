from bims.models import (
    FbisUUID,
)
import sqlite3
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from geonode.people.models import Profile
from bims.models import LocationSite
from sass.models import SiteVisit
from sass.scripts.fbis_importer import FbisImporter
from sass.enums.canopy_cover import CanopyCover
from sass.enums.water_level import WaterLevel, WATER_LEVEL_NAME
from sass.enums.water_turbidity import WaterTurbidity


class FbisSiteVisitImporter(FbisImporter):

    canopy_cover = {}
    water_level = {}
    water_turbidity = {}
    content_type_model = SiteVisit
    table_name = 'SiteVisit'

    def start_processing_rows(self):
        conn =  sqlite3.connect(self.sqlite_filepath)
        cur = conn.cursor()
        cur.execute('SELECT * FROM CANOPYCOVER')
        canopy_cover_rows = cur.fetchall()
        cur.close()
        for canopy_cover in canopy_cover_rows:
            for canopy in CanopyCover:
                if canopy.value == canopy_cover[1]:
                    self.canopy_cover[canopy_cover[0]] = canopy

        cur = conn.cursor()
        cur.execute('SELECT * FROM WATERLEVEL')
        water_level_rows = cur.fetchall()
        cur.close()
        for water_level_row in water_level_rows:
            for water_level in WaterLevel:
                if water_level.value[WATER_LEVEL_NAME] == water_level_row[1]:
                    self.water_level[water_level_row[0]] = water_level

        cur = conn.cursor()
        cur.execute('SELECT * FROM WATERTURBIDITY')
        water_turbidity_rows = cur.fetchall()
        cur.close()
        for water_turbidity_row in water_turbidity_rows:
            for water_turbidity in WaterTurbidity:
                if water_turbidity.value == water_turbidity_row[1]:
                    self.water_turbidity[water_turbidity_row[0]] = (
                        water_turbidity
                    )

    def process_row(self, row, index):
        # Get site id
        site_ctype = ContentType.objects.get_for_model(LocationSite)
        site = None
        sites = FbisUUID.objects.filter(
            uuid=self.get_row_value('SiteID', row),
            content_type=site_ctype
        )
        if sites.exists():
            site = sites[0].content_object
        if not site:
            print('Missing Site')
            return

        user_ctype = ContentType.objects.get_for_model(
            Profile
        )
        assessor = None
        users = FbisUUID.objects.filter(
            uuid=self.get_row_value('AssessorID', row),
            content_type=user_ctype
        )
        if users.exists():
            assessor = users[0].content_object

        water_level_value = self.get_row_value('WaterLevelID', row)
        water_level = None
        if water_level_value:
            water_level = self.water_level[water_level_value].name

        water_turbidity = None
        water_turbidity_value = self.get_row_value('WaterTurbidityID', row)
        if water_turbidity_value:
            water_turbidity = self.water_turbidity[water_turbidity_value].name

        canopy_cover = None
        canopy_cover_value = self.get_row_value('CanopyCoverID', row)
        if canopy_cover_value:
            canopy_cover = self.canopy_cover[canopy_cover_value].name

        site_visit, created = SiteVisit.objects.get_or_create(
            location_site=site,
            site_visit_date=datetime.strptime(
                self.get_row_value('SiteVisit', row),
                '%m/%d/%y %H:%M:%S'
            ),
            assessor=assessor,
            water_level=water_level,
            water_turbidity=water_turbidity,
            canopy_cover=canopy_cover,
            average_velocity=self.get_row_value('Average Velocity', row, True),
            average_depth=self.get_row_value('Average Depth', row, True),
            discharge=self.get_row_value('Discharge', row, True),
            sass_version=self.get_row_value('SASSDataVersion', row, True)
        )

        site_visit.additional_data = {
            'CanopyCoverComment': self.get_row_value(
                'CanopyCoverComment',
                row
            ),
            'SASSDataComment': self.get_row_value(
                'SASSDataComment',
                row
            ),
            'SampleInstitute': self.get_row_value(
                'SampleInstitute',
                row
            ),
            'Prev': self.get_row_value('Prev', row),
            'Frozen': self.get_row_value('Frozen', row)
        }
        site_visit.save()

        self.save_uuid(
            uuid=self.get_row_value('SiteVisitID', row),
            object_id=site_visit.id
        )
