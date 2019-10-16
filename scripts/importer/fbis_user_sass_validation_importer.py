import json

from django.contrib.auth import get_user_model

from scripts.importer.fbis_postgres_importer import FbisPostgresImporter
from bims.models import Profile
from bims.utils.logger import log


class FbisUserSassValidationImporter(FbisPostgresImporter):

    content_type_model = get_user_model()
    table_name = '"UserSASSValidation"'

    def process_row(self, row, index):
        valid_from = self.get_row_value('validfrom')
        valid_to = self.get_row_value('validto')
        user = self.get_object_from_uuid(
            column='userid',
            model=get_user_model()
        )
        status = self.get_row_value('status')
        if user:
            profile, created = Profile.objects.get_or_create(
                user=user
            )
            if not profile.sass_accredited_date_from:
                profile.sass_accredited_date_from = valid_from
            else:
                if valid_from.date() > profile.sass_accredited_date_from:
                    profile.sass_accredited_date_from = valid_from
            if not profile.sass_accredited_date_to:
                profile.sass_accredited_date_to = valid_to
            else:
                if valid_to.date() > profile.sass_accredited_date_to:
                    profile.sass_accredited_date_to = valid_to
            try:
                json_data = json.loads(profile.data)
                json_data['sass_accredited_status'] = status
                profile.data = json_data
            except ValueError:
                pass
            profile.save()

            log('{user}-{valid_from}-{valid_to}-{status}'.format(
                user=profile,
                valid_from=valid_from,
                valid_to=valid_to,
                status=status
            ))
