import logging
from django.contrib.auth.models import Permission

logger = logging.getLogger(__name__)


def generate_permission(
        permission_name,
        default_permission='can_validate_data'):
    # Generate permission based on taxon class
    if not permission_name:
        return None

    logger.info('Generate permission for %s' % permission_name)
    default_permission = Permission.objects.filter(
            codename=default_permission
    )
    if not default_permission:
        return None

    permission_codename = permission_name.lower().replace(' ', '_')

    if Permission.objects.filter(
        name=permission_name,
        codename=permission_codename,
    ).exists():
        logger.error('Permission already exists')
        return Permission.objects.filter(
            name=permission_name,
            codename=permission_codename
        ).first()

    permission = default_permission[0]
    permission.pk = None
    permission.codename = permission_name.lower().replace(' ', '_')
    permission.name = permission_name
    logger.info('New permission added : %s' % permission_codename)
    permission.save()
    return permission
