=====
BIMS
=====

BIMS is a Django app.


Quick start
-----------

1. Add "bims" to your INSTALLED_APPS setting like this:

    INSTALLED_APPS = [
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'allauth.socialaccount.providers.google',
        'allauth.socialaccount.providers.github',
        'easyaudit',
        'rolepermissions',
        'rest_framework',
        'bims',
    ]

2. Include the bims URLconf in your project urls.py like this:

    path('bims/', include('bims.urls'))

3. Run `python manage.py migrate` to create the bims models.
