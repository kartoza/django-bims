=====
BIMS
=====

BIMS is a Django app.

Note that BIMS is under development and not yet feature complete.

The latest source code is available at http://github.com/kartoza/django-bims.

* **Developers:** See our `project setup guide`_ and `developer guide`_


Project Activity
----------------

|ready| |inprogress|

|throughput_graph|

* Current test status master: |test_status_master| 

* Current test status develop: |test_status_develop| 


Quick Project Setup
-------------------

Refer to `project setup guide`_ for in depth information.

Make sure ansible is installed, all.yml file is configured, and project
already opened using PyCharm. Then run these command:

    make ansible-check

This will check and dry-run ansible tasks

    make setup-ansible

This will generate project file configuration.


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



Generating boundaries
---------------------------
Bims using boundaries for clustering. To generate it, do

    make generate-boundaries


Thank you
_________

Thank you to the individual contributors who have helped to build HealthyRivers:

* Tim Sutton (Lead developer): tim@kartoza.com
* Dimas Ciptura: dimas@kartoza.com
* Irwan Fathurrahman: irwan@kartoza.com
* Anita Hapsari: anita@kartoza.com

.. _developer guide: https://github.com/kartoza/django-bims/blob/develop/README-dev.md
.. _docker: http://docker.com
.. _project setup guide: deployment/ansible/README.md
.. |ready| image:: https://badge.waffle.io/kartoza/django-bims.svg?label=ready&title=Ready
.. |inprogress| image:: https://badge.waffle.io/kartoza/django-bims.svg?label=in%20progress&title=In%20Progress
.. |throughput_graph| image:: https://graphs.waffle.io/kartoza/django-bims/throughput.svg
.. |test_status_master| image:: https://travis-ci.org/kartoza/django-bims.svg?branch=master
.. |test_status_develop| image:: https://travis-ci.org/kartoza/django-bims.svg?branch=develop
.. |nbsp| unicode:: 0xA0
   :trim:
