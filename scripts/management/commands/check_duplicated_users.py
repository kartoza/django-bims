# -*- coding: utf-8 -*-
import logging
import os
import csv
import json
from allauth.utils import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models.functions import Lower
from django.conf import settings
from django.db.models.fields.related import ForeignObjectRel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Check duplication in users data,
    following parameters are used to indicate the duplication :
    - email
    - user_name
    If duplicates found, get the latest user, then update all references to
    the latest user. Remove old users.
    """

    def handle(self, *args, **options):
        User = get_user_model()
        user_with_duplicates = User.objects.exclude(
            email=''
        ).annotate(
            lemail=Lower('email')
        ).values('lemail').annotate(
            count=Count(Lower('email'))
        ).values('lemail', 'count').filter(
            count__gt=1
        ).order_by(
            'lemail', 'count'
        )

        csv_path = os.path.join(settings.MEDIA_ROOT, 'duplicated_users.csv')
        links = []

        with open(csv_path, mode='w') as csv_file:
            writer = csv.writer(
                csv_file, delimiter=',', quotechar='"',
                quoting=csv.QUOTE_MINIMAL)
            writer.writerow([
                'Email', 'Count', 'Latest'
            ])
            for duplicate in user_with_duplicates:
                csv_row = [
                    duplicate['lemail'],
                    duplicate['count']
                ]

                users = User.objects.filter(
                    email__iexact=duplicate['lemail']
                ).order_by('last_login', '-date_joined')

                latest_user = users[0]

                # Get the oldest sass_accredited date from
                sass_accredited_date_from_user = User.objects.filter(
                    email__iexact=duplicate['lemail']
                ).exclude(
                    bims_profile__sass_accredited_date_from__isnull=True
                ).order_by(
                    'bims_profile__sass_accredited_date_from'
                )

                # -- Get the most recent sass_accredited_date_to
                sass_accredited_date_to_user = User.objects.filter(
                    email__iexact=duplicate['lemail']
                ).exclude(
                    bims_profile__sass_accredited_date_to__isnull=True
                ).order_by(
                    '-bims_profile__sass_accredited_date_to'
                )

                date_from = latest_user.bims_profile.sass_accredited_date_from
                date_to = latest_user.bims_profile.sass_accredited_date_to

                try:
                    if sass_accredited_date_from_user.count() > 0:
                        date_from = sass_accredited_date_from_user[0].bims_profile.sass_accredited_date_from
                except Exception as e:
                    pass
                try:
                    if sass_accredited_date_to_user.count() > 0:
                        date_to = sass_accredited_date_to_user[0].bims_profile.sass_accredited_date_to
                except Exception as e:
                    pass

                latest_user.bims_profile.sass_accredited_date_from = date_from
                latest_user.bims_profile.sass_accredited_date_to = date_to
                latest_user.bims_profile.save()

                if not links:
                    links = [
                        rel.get_accessor_name() for rel in latest_user._meta.get_fields() if issubclass(type(rel), ForeignObjectRel)
                    ]

                if links:
                    for user in users[1:]:
                        print('----- {} -----'.format(str(user)))
                        for link in links:
                            try:
                                objects = getattr(user, link).all()
                                if objects.count() > 0:
                                    print('Updating {obj} for User : {user}'.format(
                                        obj=str(objects.model._meta.label),
                                        user=str(user)
                                    ))
                                    update_dict = {
                                        getattr(user, link).field.name : latest_user
                                    }
                                    objects.update(**update_dict)
                            except Exception as e:  # noqa
                                continue
                        print(''.join(['-' for i in range(len(str(user)) + 12)]))
                csv_row.append(
                    json.dumps({
                        'username': latest_user.username,
                        'last_login': str(latest_user.last_login),
                        'date_joined': str(latest_user.date_joined),
                        'date_from': str(date_from) if date_from else '-',
                        'date_to': str(date_to) if date_to else '-'
                    })
                )

                writer.writerow(csv_row)

                users.exclude(id=latest_user.id).delete()
