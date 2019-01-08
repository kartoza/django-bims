import os
import pandas_access as mdb
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from bims.models import (
    FbisUUID,
)
from sass.models import River


def import_river_table(accdb_file_name):
    accdb_filepath = os.path.join(
        settings.MEDIA_ROOT,
        accdb_file_name
    )
    if not os.path.isfile(accdb_filepath):
        print('%s not found in media directory' % accdb_file_name)
        return

    # Read User table.
    df = mdb.read_table(
        accdb_filepath,
        'River',
        promote='nullable_int_to_float')
    dhead = df.head(len(df))
    ctype = ContentType.objects.get_for_model(River)

    for i in range(len(dhead)):
        print('Processing %s of %s' % (i, len(dhead)))
        validated_value = str(dhead['Validated'][i]) == '1.0'

        # Get owner
        owner = None
        owners = FbisUUID.objects.filter(
            uuid=dhead['OwnerID'][i]
        )
        if owners.exists():
            owner = owners[0].content_object

        river, created = River.objects.get_or_create(
            name=dhead['RiverName'][i],
            owner=owner
        )
        river.validated = validated_value
        river.save()

        fbis_uuid, uuid_created = FbisUUID.objects.get_or_create(
            content_type=ctype,
            object_id=river.id,
            uuid=dhead['RiverID'][i]
        )
