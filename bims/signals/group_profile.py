from __future__ import absolute_import
from django.db.models.signals import post_save
from django.dispatch import receiver
from geonode.people.models import Profile
from django.db import transaction


def on_transaction_commit(func):
    def inner(*args, **kwargs):
        transaction.on_commit(lambda: func(*args, **kwargs))

    return inner


@receiver(post_save, sender=Profile)
@on_transaction_commit
def update_group_profile_members(instance, sender, **kwargs):
    """
    Makes sure the group profile is also updated
    """
    from geonode.groups.models import GroupProfile, GroupMember
    if not instance.groups:
        return

    if instance == instance.get_anonymous():
        # The invited user cannot be anonymous
        return

    member_joined = []

    for user_group in instance.groups.all():
        try:
            group = GroupProfile.objects.get(group=user_group)
            member, created = GroupMember.objects.get_or_create(
                    group=group,
                    user=instance)
            # Give member role as default
            if not member.role:
                member.role = GroupMember.MEMBER
                member.save()
            member_joined.append(member)
        except GroupProfile.DoesNotExist:
            continue

    for group_member in GroupMember.objects.filter(user=instance):
        if group_member not in member_joined:
            group_member.delete()
