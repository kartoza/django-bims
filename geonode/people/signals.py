#########################################################################
#
# Copyright (C) 2017 OSGeo
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

"""Signal handlers pertaining to the people app

Some of these signals deal with authentication related workflows.

"""
import logging

from django.contrib.auth import get_user_model
from django.db.models import Q

from geonode.notifications_helper import send_notification


logger = logging.getLogger(__name__)



def notify_admins_new_signup(sender, **kwargs):
    staff = get_user_model().objects.filter(Q(is_active=True) & (Q(is_staff=True) | Q(is_superuser=True)))
    send_notification(
        users=staff,
        label="account_approve",
        extra_context={"from_user": kwargs["user"]}
    )


def profile_post_save(instance, sender, **kwargs):
    """
    Make sure the user belongs by default to the anonymous group.
    This will make sure that anonymous permissions will be granted to the new users.
    """
    from django.contrib.auth.models import Group
    anon_group, created = Group.objects.get_or_create(name='anonymous')
    instance.groups.add(anon_group)


    # do not create email, when user-account signup code is in use
    if getattr(instance, '_disable_account_creation', False):
        return
