from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models import Count


class Command(BaseCommand):
    help = 'Fix duplicate ContentType entries after database restore'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Checking for duplicate ContentType entries...'))

        # Find duplicates
        duplicates = (
            ContentType.objects
            .values('app_label', 'model')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        if not duplicates:
            self.stdout.write(self.style.SUCCESS('No duplicate ContentType entries found.'))
            return

        self.stdout.write(self.style.WARNING(f'Found {duplicates.count()} duplicate ContentType groups'))

        total_removed = 0

        for duplicate in duplicates:
            app_label = duplicate['app_label']
            model = duplicate['model']
            count = duplicate['count']

            self.stdout.write(f'\nProcessing {app_label}.{model} ({count} duplicates)')

            # Get all ContentType objects for this app_label/model pair
            content_types = ContentType.objects.filter(
                app_label=app_label,
                model=model
            ).order_by('id')

            # Keep the first one (lowest ID)
            keep = content_types.first()
            to_remove = content_types.exclude(id=keep.id)

            self.stdout.write(f'  Keeping ContentType ID: {keep.id}')

            # Update all foreign key references to point to the one we're keeping
            for ct in to_remove:
                self.stdout.write(f'  Removing ContentType ID: {ct.id}')

                # Update auth_permission
                with connection.cursor() as cursor:
                    cursor.execute(
                        'UPDATE auth_permission SET content_type_id = %s WHERE content_type_id = %s',
                        [keep.id, ct.id]
                    )
                    updated = cursor.rowcount
                    if updated:
                        self.stdout.write(f'    Updated {updated} auth_permission records')

                    # Update django_admin_log
                    cursor.execute(
                        'UPDATE django_admin_log SET content_type_id = %s WHERE content_type_id = %s',
                        [keep.id, ct.id]
                    )
                    updated = cursor.rowcount
                    if updated:
                        self.stdout.write(f'    Updated {updated} django_admin_log records')

                    # Update guardian_userobjectpermission
                    cursor.execute(
                        'UPDATE guardian_userobjectpermission SET content_type_id = %s WHERE content_type_id = %s',
                        [keep.id, ct.id]
                    )
                    updated = cursor.rowcount
                    if updated:
                        self.stdout.write(f'    Updated {updated} guardian_userobjectpermission records')

                    # Update guardian_groupobjectpermission
                    cursor.execute(
                        'UPDATE guardian_groupobjectpermission SET content_type_id = %s WHERE content_type_id = %s',
                        [keep.id, ct.id]
                    )
                    updated = cursor.rowcount
                    if updated:
                        self.stdout.write(f'    Updated {updated} guardian_groupobjectpermission records')

                # Delete the duplicate
                ct.delete()
                total_removed += 1

        # Remove duplicate permissions that may have been created
        self.stdout.write('\nRemoving duplicate permissions...')
        from django.contrib.auth.models import Permission

        permission_duplicates = (
            Permission.objects
            .values('content_type', 'codename')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        for perm_dup in permission_duplicates:
            perms = Permission.objects.filter(
                content_type_id=perm_dup['content_type'],
                codename=perm_dup['codename']
            ).order_by('id')

            keep_perm = perms.first()
            to_remove_perms = perms.exclude(id=keep_perm.id)

            for perm in to_remove_perms:
                self.stdout.write(f'  Removing duplicate permission: {perm}')

                # Update user_permissions M2M
                with connection.cursor() as cursor:
                    cursor.execute(
                        'UPDATE auth_user_user_permissions SET permission_id = %s WHERE permission_id = %s',
                        [keep_perm.id, perm.id]
                    )
                    # Handle constraint violations by deleting duplicates
                    cursor.execute(
                        'DELETE FROM auth_user_user_permissions WHERE permission_id = %s',
                        [perm.id]
                    )

                    # Update group_permissions M2M
                    cursor.execute(
                        'UPDATE auth_group_permissions SET permission_id = %s WHERE permission_id = %s',
                        [keep_perm.id, perm.id]
                    )
                    # Handle constraint violations by deleting duplicates
                    cursor.execute(
                        'DELETE FROM auth_group_permissions WHERE permission_id = %s',
                        [perm.id]
                    )

                perm.delete()

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully removed {total_removed} duplicate ContentType entries'))
        self.stdout.write(self.style.SUCCESS('You can now run migrations successfully'))
