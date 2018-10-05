from django.contrib.auth.models import Permission


def generate_permission(class_name):
    # Generate permission based on taxon class
    if not class_name:
        return None

    print('Generate permission for %s' % class_name)
    default_permission = Permission.objects.filter(
            codename='can_validate_data'
    )
    if not default_permission:
        return None

    permission_codename = 'can_validate_%s' % (
        class_name.lower().replace(' ', '_')
    )
    permission_name = 'Can validate %s' % (
        class_name
    )

    if Permission.objects.filter(
        name=permission_name,
        codename=permission_codename,
    ).exists():
        print('Permission already exists')
        return None

    permission = default_permission[0]
    permission.pk = None
    permission.codename = 'can_validate_%s' % (
        class_name.lower().replace(' ', '_')
    )
    permission.name = 'Can validate %s' % (
        class_name
    )
    print('New permission added : %s' % permission_codename)
    permission.save()
    return permission
