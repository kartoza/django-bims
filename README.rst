=====
BIMS
=====

BIMS is a Django app.

Note that BIMS is under development and not yet feature complete.

The latest source code is available at
[http://github.com/kartoza/django-bims](https://github.com/kartoza/django-bims).

* **Developers:** See our [developer guide](README-dev.md)


## Project Activity

* [![Stories in Ready](https://badge.waffle.io/kartoza/django-bims.svg?label=ready&title=Ready)](http://waffle.io/kartoza/django-bims)
* [![Stories in In Progress](https://badge.waffle.io/kartoza/django-bims.svg?label=in%20progress&title=In%20Progress)](http://waffle.io/kartoza/django-bims)

[![Throughput Graph](https://graphs.waffle.io/kartoza/django-bims/throughput.svg)](https://waffle.io/kartoza/django-bims/metrics)

* Current test status master: [![Build Status](https://travis-ci.org/kartoza/django-bims.svg?branch=master)](https://travis-ci.org/kartoza/django-bims)

* Current test status develop: [![Build Status](https://travis-ci.org/inasafe/django-bimx.svg?branch=develop)](https://travis-ci.org/kartoza/django-bims)


Quick Installation Guide
------------------------
For deployment we use [docker](http://docker.com) so you need to have docker
running on the host. HealthyRivers is a django app so it will help if you have
some knowledge of running a django site.

```
git clone git://github.com/kartoza/django-bims.git
make build
make permissions
make web
# Wait a few seconds for the DB to start before to do the next command
make migrate
make collectstatic
```

So as to create your admin account:
```
make superuser
```


Install as a Django Package
---------------------------

1. Add "bims" to your INSTALLED_APPS setting like this:

    INSTALLED_APPS = [
        'bims',
    ]

2. Include the bims URLconf in your project urls.py like this:

    path('bims/', include('bims.urls'))

3. Run `python manage.py migrate` to create the bims models.


Thank you
_________

Thank you to the individual contributors who have helped to build HealthyRivers:

* Christian Christelis (Lead developer): christian@kartoza.com
* Tim Sutton (Lead developer): tim@kartoza.com
* Dimas Ciptura: dimas@kartoza.com
* Irwan Fathurrahman: irwan@kartoza.com
* Anita Hapsari: anita@kartoza.com
