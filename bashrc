#!/bin/bash

# This is intended to be placed in the docker dev environment so
# that the django project is in the path when you log in

if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi
export PYTHONPATH=/home/web/django_project:$PYTHONPATH
cd /home/web/django_project
