# coding=utf-8

"""Helpers for settings."""
import os

# Absolute filesystem path to the Django project directory:
DJANGO_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ))


def absolute_path(*args):
    """Get an absolute path for a file that is relative to the django root.

    :param args: List of path elements.
    :type args: list

    :returns: An absolute path.
    :rtype: str
    """
    return os.path.join(DJANGO_ROOT, *args)


def ensure_secret_key_file():
    """Checks that secret.py exists in settings dir.

    If not, creates one with a random generated SECRET_KEY setting."""
    secret_path = absolute_path('core', 'settings', 'secret.py')
    if not os.path.exists(secret_path):
        from django.utils.crypto import get_random_string
        secret_key = get_random_string(
            50, 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
        with open(secret_path, 'w') as f:
            f.write("SECRET_KEY = " + repr(secret_key) + "\n")


def ensure_unique_app_labels(installed_apps):
    """Checks that INSTALLED APPS contains unique app labels."""
    retval = ()
    for val in installed_apps:
        if val in retval:
            continue
        retval += (val, )
    return retval


def extract_replicas(replica_env_var):
    replicas = []
    if replica_env_var:
        replica_details = replica_env_var.split(",")
        for detail in replica_details:
            user, password_host_port_name = detail.split(":", 1)
            password, host_port_name = password_host_port_name.split("@", 1)
            host_port, name = host_port_name.rsplit("/", 1)
            host, port = host_port.rsplit(":", 1)
            replicas.append({
                'ENGINE': 'django_tenants.postgresql_backend',
                'USER': user,
                'PASSWORD': password,
                'HOST': host,
                'PORT': port,
                'NAME': name,
            })
    return replicas


# Import the secret key
ensure_secret_key_file()
