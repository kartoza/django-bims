from datetime import datetime
from django.db.models import signals, Q
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError
from easyaudit.signals.model_signals import pre_save as easyaudit_presave
from geonode.people.models import Profile
from sass.models import SiteVisitTaxon, SiteVisit, SassTaxon, TaxonAbundance
from scripts.importer.fbis_importer import FbisImporter


class FbisSiteVisitTaxonImporter(FbisImporter):

    content_type_model = SiteVisitTaxon
    table_name = 'SiteVisitTaxon'
    success = 0
    failed = 0
    user_table_columns = None
    temp_table_columns = None
    user_conn = None

    def get_user_table_columns(self):
        cur = self.user_conn.cursor()
        sql = "SELECT * FROM User WHERE 1=0"
        cur.execute(sql)
        self.user_table_columns = [d[0] for d in cur.description]
        cur.close()

    def get_user_from_id(self, user_id):
        cur = self.user_conn.cursor()
        table_name = 'User'
        sql = "SELECT * FROM {table_name} WHERE UserID='{user_id}'".format(
            table_name=table_name,
            user_id=str(user_id)
        )
        cur.execute(sql)
        data = cur.fetchone()
        cur.close()
        return data

    def start_processing_rows(self):
        signals.pre_save.disconnect(
            easyaudit_presave,
            dispatch_uid='easy_audit_signals_pre_save'
        )

    def finish_processing_rows(self):
        signals.pre_save.connect(
            easyaudit_presave,
            dispatch_uid='easy_audit_signals_pre_save'
        )
        print('New Data total : {}'.format(len(self.new_data)))
        print('New Data : {}'.format(self.new_data))
        print('Failed Total : {}'.format(self.failed))
        print('Failed Messages : {}'.format(self.failed_messages))

    def process_row(self, row, index):

        site_visit_taxon = self.get_object_from_uuid(
            column='SiteVisitTaxonID',
            model=SiteVisitTaxon
        )

        if self.only_missing and site_visit_taxon:
            print('{} already exist'.format(site_visit_taxon))
            return

        site_visit = self.get_object_from_uuid(
            column='SiteVisitID',
            model=SiteVisit
        )

        if not site_visit:
            self.failed_messages.append('Missing site visit - {}'.format(
                row
            ))
            return

        sass_taxon = self.get_object_from_uuid(
            column='TaxonID',
            model=SassTaxon
        )
        if not sass_taxon:
            self.failed_messages.append(
                'Missing sass taxon - {}'.format(row)
            )
            return

        taxon_abundance = self.get_object_from_uuid(
            column='TaxonAbundanceID',
            model=TaxonAbundance
        )

        collection_date = datetime.strptime(
            self.get_row_value('DateFrom'),
            '%m/%d/%y %H:%M:%S'
        )

        user_id = self.get_row_value('UserID')
        if not user_id:
            user_id = self.get_row_value('User')

        user = self.get_object_from_uuid(
            column='User',
            model=Profile,
            uuid=user_id
        )

        if not user:
            if not self.user_table_columns:
                self.user_conn = self.create_connection()
                self.get_user_table_columns()
            user_data = self.get_user_from_id(self.get_row_value('User'))
            self.temp_table_columns = self.table_colums
            self.table_colums = self.user_table_columns
            username = self.get_row_value('UserName', user_data).replace(
                ' ', '_').lower()

            # Check if user already exist
            profile = Profile.objects.filter(
                Q(username=username) |
                Q(first_name=self.get_row_value('FirstName', user_data),
                  last_name=self.get_row_value('Surname', user_data)) |
                Q(email=self.get_row_value('Email', user_data))
            )

            temp_content_type = self.content_type
            self.content_type = ContentType.objects.get_for_model(
                Profile)
            if profile.exists():
                user = profile[0]
                self.save_uuid(
                    uuid=user_id,
                    object_id=user.id
                )
            else:
                self.create_user_from_row(user_data, user_id)
                user = self.get_object_from_uuid(
                    column='User',
                    model=Profile,
                    uuid=user_id
                )
            self.content_type = temp_content_type
            self.table_colums = self.temp_table_columns

        try:
            site_visit_taxon, created = SiteVisitTaxon.objects.get_or_create(
                site=site_visit.location_site,
                collection_date=collection_date,
                taxonomy=sass_taxon.taxon,
                taxon_abundance=taxon_abundance,
                site_visit=site_visit
            )
            site_visit_taxon.collector = user.username
            site_visit_taxon.owner = user
            site_visit_taxon.sass_taxon = sass_taxon
            site_visit_taxon.institution_id='fbis'
            site_visit_taxon.source_collection='fbis'
            site_visit_taxon.notes='From SASS'
            site_visit_taxon.save()
            if created:
                self.new_data.append(site_visit_taxon.id)
            else:
                print('{} already exist'.format(site_visit_taxon))
        except (ValueError, IntegrityError, AttributeError) as e:
            self.failed += 1
            print('Error - {}'.format(str(e)))
            self.failed_messages.append(
                '{error} - {row}'.format(
                    error=str(e),
                    row=row
                )
            )
            return

        self.save_uuid(
            uuid=self.get_row_value('SiteVisitTaxonID', row),
            object_id=site_visit_taxon.id
        )
