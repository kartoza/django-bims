=====
BIMS
=====

BIMS is a Django app.


Quick start
-----------

1. Add "bims" to your INSTALLED_APPS setting like this:

    INSTALLED_APPS = [
        'bims',
    ]

2. Include the bims URLconf in your project urls.py like this:

    path('bims/', include('bims.urls'))

3. Run `python manage.py migrate` to create the bims models.
