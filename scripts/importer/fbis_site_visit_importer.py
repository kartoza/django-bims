import psycopg2 as driv
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, signals
from geonode.people.models import Profile
from bims.models import LocationSite
from sass.models import SiteVisit, site_visit_post_save_handler
from scripts.importer.fbis_importer import FbisImporter
from sass.enums.canopy_cover import CanopyCover
from sass.enums.water_level import WaterLevel, WATER_LEVEL_NAME
from sass.enums.water_turbidity import WaterTurbidity
from sass.enums.channel_type import ChannelType, CHANNEL_TYPE_NAME
from bims.models import (
    FbisUUID,
)


class FbisSiteVisitImporter(FbisImporter):

    canopy_cover = {}
    water_level = {}
    water_turbidity = {}
    channel_type = {}
    embeddedness = {}
    content_type_model = SiteVisit
    table_name = 'SiteVisit'

    def finish_processing_rows(self):
        print('New Data total : {}'.format(len(self.new_data)))
        print('New Data : {}'.format(self.new_data))
        print('Failed Total : {}'.format(len(self.failed_messages)))
        print('Failed Messages : {}'.format(self.failed_messages))

    def start_processing_rows(self):
        if self.update_only:
            signals.post_save.disconnect(
                site_visit_post_save_handler,
                sender=SiteVisit
            )
        if self.is_sqlite:
            conn = self.create_connection()
        else:
            conn = driv.connect(database=self.postgres_database,
                            user=self.postgres_user,
                            password=self.postgres_password,
                            host=self.postgres_host,
                            port=self.postgres_port)
        cur = conn.cursor()
        cur.execute('SELECT * FROM canopycover')
        canopy_cover_rows = cur.fetchall()
        cur.close()
        for canopy_cover in canopy_cover_rows:
            for canopy in CanopyCover:
                if canopy.value == canopy_cover[1]:
                    self.canopy_cover[canopy_cover[0]] = canopy

        cur = conn.cursor()
        cur.execute('SELECT * FROM embeddedness')
        embeddedness_rows = cur.fetchall()
        cur.close()
        for embeddedness_row in embeddedness_rows:
            for embeddedness_choice in SiteVisit.EMBEDDEDNESS_CHOICES:
                if embeddedness_choice[0] == embeddedness_row[1].encode('utf-8'):
                    self.embeddedness[embeddedness_row[0]] = (
                        embeddedness_choice
                    )

        cur = conn.cursor()
        cur.execute('SELECT * FROM waterlevel')
        water_level_rows = cur.fetchall()
        cur.close()
        for water_level_row in water_level_rows:
            for water_level in WaterLevel:
                if water_level.value[WATER_LEVEL_NAME] == water_level_row[1]:
                    self.water_level[water_level_row[0]] = water_level

        cur = conn.cursor()
        cur.execute('SELECT * FROM waterturbidity')
        water_turbidity_rows = cur.fetchall()
        cur.close()
        for water_turbidity_row in water_turbidity_rows:
            for water_turbidity in WaterTurbidity:
                if water_turbidity.value == water_turbidity_row[1]:
                    self.water_turbidity[water_turbidity_row[0]] = (
                        water_turbidity
                    )

        cur = conn.cursor()
        cur.execute('SELECT * FROM channeltype')
        channel_type_rows = cur.fetchall()
        cur.close()
        for channel_type_row in channel_type_rows:
            for channel_type in ChannelType:
                if channel_type.value[
                    CHANNEL_TYPE_NAME] == channel_type_row[1]:
                    self.channel_type[channel_type_row[0]] = channel_type

    def process_row(self, row, index):
        site_visit = self.get_object_from_uuid(
            column='SiteVisitID',
            model=SiteVisit
        )

        if self.only_missing and site_visit:
            print('{} already exist'.format(site_visit))
            return

        # Get site id
        site_ctype = ContentType.objects.get_for_model(LocationSite)

        if self.update_only:
            site_visit_ctype = ContentType.objects.get_for_model(SiteVisit)
            site_visit_uuid = self.get_row_value('sitevisitid')
            uuids = site_visit_uuid.split('-')
            uuids[0] = '%s%s' % (uuids[0][4:], uuids[0][:4])
            uuids[3] = '%s%s' % (uuids[3][2:], uuids[3][:2])
            uuids[4] = '%s%s%s%s%s%s' % (uuids[4][2:4], uuids[4][:2],
                                         uuids[4][6:8], uuids[4][4:6],
                                         uuids[4][10:], uuids[4][8:10])
            new_uuids = '-'.join(uuids)
            site_visits = FbisUUID.objects.filter(
                Q(uuid__icontains=new_uuids) |
                Q(uuid__icontains=site_visit_uuid),
                content_type=site_visit_ctype
            )
            if not site_visits.exists():
                print('Site Visit does not exist')
                return
            try:
                site_visit = SiteVisit.objects.get(
                    id=site_visits[0].object_id
                )
            except SiteVisit.DoesNotExist:
                print('Site Visit does not exist for FBISuuid : %s' %
                      site_visits[0].id)
                return

            embeddedness_value = self.get_row_value('embeddednessid', row)
            if embeddedness_value:
                site_visit.embeddedness = (
                    self.embeddedness[embeddedness_value][0]
                )
                site_visit.save()
                print('embeddedness updated for SiteVisit with id : %s'
                      % site_visit.id)
            return

        site = self.get_object_from_uuid(
            column='SiteID',
            model=LocationSite
        )
        if not site:
            sites = FbisUUID.objects.filter(
                uuid__icontains=self.get_row_value('SiteID', row),
                content_type=site_ctype
            )
            if sites.exists():
                site = sites[0].content_object
        if not site:
            print('Missing Site')
            self.failed_messages.append('Missing site {}'.format(row))
            return

        user_ctype = ContentType.objects.get_for_model(
            Profile
        )
        owner = None
        users = FbisUUID.objects.filter(
            uuid=self.get_row_value('AssessorID', row),
            content_type=user_ctype
        )
        if users.exists():
            owner = users[0].content_object

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
            water_level=water_level,
            water_turbidity=water_turbidity,
            canopy_cover=canopy_cover,
            average_velocity=self.get_row_value('Average Velocity', row, True),
            average_depth=self.get_row_value('Average Depth', row, True),
            discharge=self.get_row_value('Discharge', row, True),
            sass_version=self.get_row_value('SASSDataVersion', row, True)
        )

        site_visit.owner = owner

        if created:
            self.new_data.append(site_visit.id)

        site_visit.additional_data = {
            'CanopyCoverComment': self.get_row_value(
                'CanopyCoverComment'
            ),
            'SASSDataComment': self.get_row_value(
                'SASSDataComment'
            ),
            'SampleInstitute': self.get_row_value(
                'SampleInstitute'
            ),
            'Prev': self.get_row_value('Prev'),
            'Frozen': self.get_row_value('Frozen'),
            'FishOwner': self.get_row_value('FishOwner'),
            'FishAssessor': self.get_row_value('FishAssessor'),
            'RipirianOwner': self.get_row_value('RipirianOwner'),
            'RipirianAssessor': self.get_row_value('RipirianAssessor'),
            'InvertebrateOwner': self.get_row_value('InvertebrateOwner'),
            'InvertebrateAssessor': self.get_row_value('InvertebrateAssessor'),
            'WaterChemistryOwner': self.get_row_value('WaterChemistryOwner'),
            'WaterChemistryAssessor': self.get_row_value(
                'WaterChemistryAssessor'),
        }

        channel_type = None
        channel_type_value = self.get_row_value('ChannelTypeID')
        if channel_type_value:
            channel_type = self.channel_type[channel_type_value].name
        site_visit.channel_type = channel_type
        site_visit.save()

        self.save_uuid(
            uuid=self.get_row_value('SiteVisitID', row),
            object_id=site_visit.id
        )
