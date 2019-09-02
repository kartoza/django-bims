from paver.easy import (cmdopts, options,sh, task)

@task
@cmdopts([
    ('settings=', 's', 'Specify custom DJANGO_SETTINGS_MODULE')
])
def import_fbis_data():
    settings = options.get('settings', '')
    if settings and 'DJANGO_SETTINGS_MODULE' not in settings:
        settings = 'DJANGO_SETTINGS_MODULE=%s' % settings

    sh("%s python manage.py migrate_site_owners" %
       settings)
    sh("%s python manage.py import_fbis_reference_doi" %
       settings)
