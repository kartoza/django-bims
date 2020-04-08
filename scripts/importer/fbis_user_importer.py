# -*- coding: utf-8 -*-
from geonode.people.models import Profile
from bims.models.profile import Profile as BimsProfile
from scripts.importer.fbis_postgres_importer import FbisPostgresImporter


class FbisUserImporter(FbisPostgresImporter):

    content_type_model = Profile
    table_name = '"User"'

    def process_row(self, row, index):
        # print(row)
        self.create_user_from_row(row)
