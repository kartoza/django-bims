import json
from datetime import datetime

from django.contrib.auth import get_user_model

from sass.scripts.fbis_importer import FbisImporter
from bims.models import Profile
from bims.utils.logger import log


class FbisUserSassValidationImporter(FbisImporter):

    content_type_model = get_user_model()
    table_name = 'UserSASSValidation'

    def process_row(self, row, index):
        valid_from = datetime.strptime(
            self.get_row_value('ValidFrom'),
            '%m/%d/%y %H:%M:%S'
        )
        valid_to = datetime.strptime(
            self.get_row_value('ValidTo'),
            '%m/%d/%y %H:%M:%S'
        )
        user = self.get_object_from_uuid(
            column='UserID',
            model=get_user_model()
        )
        status = self.get_row_value('Status')
        if user:
            profile, created = Profile.objects.get_or_create(
                user=user
            )
            profile.sass_accredited_date_from = valid_from
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
