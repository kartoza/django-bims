=====
BIMS
=====

.. image:: https://badges.gitter.im/django-bims/community.svg
   :alt: Join the chat at https://gitter.im/django-bims/community
   :target: https://gitter.im/django-bims/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

BIMS is a Django app.

Note that BIMS is under development and not yet feature complete.

The latest source code is available at http://github.com/kartoza/django-bims.

* **Developers:** See our `project setup guide`_ and `developer guide`_


Project Activity
----------------

|Test Badge| 

|Build Badge|


Quick Installation Guide
------------------------
For deployment we use `docker`_ so you need to have docker
running on the host. HealthyRivers is a django app so it will help if you have
some knowledge of running a django site.

    git clone git://github.com/kartoza/django-bims.git
    
    make build
    
    make permissions
    
    make web
    
    # Wait a few seconds for the DB to start before to do the next command
    
    make migrate
    
    make collectstatic

    # Finally we can rebuild our search indexes if needed

    make rebuildindex
    

So as to create your admin account:
```
make superuser
```



Optional keys on project
---------------------------
To use some feature, there are keys that needs to be included on the project.
Please put the keys on the secret.py

The keys are:

1. To show bing map, use your key of bing (https://www.bingmapsportal.com/) and put it in `core/settings/secret.py` with key BING_MAP_KEY

2. To show openmaptile map (terrain and other style), use your key of maptile (https://www.maptiler.com/cloud/) and put it in `core/settings/secret.py` with key MAP_TILER_KEY



Thank you
_________

Thank you to the individual contributors who have helped to build HealthyRivers:

* Tim Sutton (Lead developer): tim@kartoza.com
* Dimas Ciputra: dimas@kartoza.com
* Irwan Fathurrahman: irwan@kartoza.com
* Fanevanjanahary: faneva@kartoza.com
* Anita Hapsari: anita@kartoza.com

.. |Test Badge| image:: https://github.com/kartoza/django-bims/actions/workflows/test.yml/badge.svg 
.. |Build Badge| image:: https://github.com/kartoza/django-bims/actions/workflows/dockerimage.yml/badge.svg
.. _developer guide: https://github.com/kartoza/django-bims/blob/develop/README-dev.md
.. _docker: http://docker.com
.. _project setup guide: deployment/ansible/README.md
.. |test_status_master| image:: https://travis-ci.org/kartoza/django-bims.svg?branch=master
.. |test_status_develop| image:: https://travis-ci.org/kartoza/django-bims.svg?branch=develop
.. |nbsp| unicode:: 0xA0
   :trim:
