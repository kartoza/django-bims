# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import logging
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission
from guardian.utils import get_user_obj_perms_model
from geonode.groups.models import GroupProfile

logger = logging.getLogger("geonode.security.utils")


def get_visible_resources(queryset,
                          user,
                          request=None,
                          admin_approval_required=False,
                          unpublished_not_visible=False,
                          private_groups_not_visibile=False):
    # Get the list of objects the user has access to
    is_admin = user.is_superuser if user and user.is_authenticated else False
    anonymous_group = None
    public_groups = GroupProfile.objects.exclude(access="private").values('group')
    groups = []
    group_list_all = []
    try:
        group_list_all = user.group_list_all().values('group')
    except Exception:
        pass

    try:
        anonymous_group = Group.objects.get(name='anonymous')
        if anonymous_group and anonymous_group not in groups:
            groups.append(anonymous_group)
    except Exception:
        pass

    filter_set = queryset

    if not is_admin:
        if admin_approval_required:
            if not user or user.is_anonymous:
                filter_set = filter_set.filter(
                    Q(is_published=True) |
                    Q(group__in=public_groups) |
                    Q(group__in=groups)
                ).exclude(Q(is_approved=False))

        # Hide Unpublished Resources to Anonymous Users
        if unpublished_not_visible:
            if not user or user.is_anonymous:
                filter_set = filter_set.exclude(Q(is_published=False))

        # Hide Resources Belonging to Private Groups
        if private_groups_not_visibile:
            private_groups = GroupProfile.objects.filter(access="private").values('group')
            if user and user.is_authenticated:
                filter_set = filter_set.exclude(
                    Q(group__in=private_groups) & ~(
                        Q(owner__username__iexact=str(user)) | Q(group__in=group_list_all))
                )
            else:
                filter_set = filter_set.exclude(group__in=private_groups)

        # Hide Dirty State Resources
        if user and user.is_authenticated:
            filter_set = filter_set.exclude(
                Q(dirty_state=True) & ~(
                    Q(owner__username__iexact=str(user)) | Q(group__in=group_list_all))
            )
        elif not user or user.is_anonymous:
            filter_set = filter_set.exclude(Q(dirty_state=True))

        if admin_approval_required or unpublished_not_visible or private_groups_not_visibile:
            _allowed_resources = []
            for _obj in filter_set.all():
                try:
                    resource = _obj.get_self_resource()
                    if user.has_perm('base.view_resourcebase', resource) or \
                    user.has_perm('view_resourcebase', resource):
                        _allowed_resources.append(resource.id)
                except (PermissionDenied, Exception) as e:
                    logger.debug(e)
            return filter_set.filter(id__in=_allowed_resources)

    return filter_set


def get_users_with_perms(obj):
    """
    Override of the Guardian get_users_with_perms
    """
    from .models import (VIEW_PERMISSIONS, ADMIN_PERMISSIONS, LAYER_ADMIN_PERMISSIONS)
    ctype = ContentType.objects.get_for_model(obj)
    permissions = {}
    PERMISSIONS_TO_FETCH = VIEW_PERMISSIONS + ADMIN_PERMISSIONS + LAYER_ADMIN_PERMISSIONS

    for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH, content_type_id=ctype.id):
        permissions[perm.id] = perm.codename

    user_model = get_user_obj_perms_model(obj)
    users_with_perms = user_model.objects.filter(object_pk=obj.pk,
                                                 content_type_id=ctype.id,
                                                 permission_id__in=permissions).values('user_id', 'permission_id')

    users = {}
    for item in users_with_perms:
        if item['user_id'] in users:
            users[item['user_id']].append(permissions[item['permission_id']])
        else:
            users[item['user_id']] = [permissions[item['permission_id']], ]

    profiles = {}
    for profile in get_user_model().objects.filter(id__in=list(users.keys())):
        profiles[profile] = users[profile.id]

    return profiles

