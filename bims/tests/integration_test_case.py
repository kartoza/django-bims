from django.core.management import call_command
from django.test import TestCase


class IntegrationTestCase(TestCase):
    def rebuild_index(self):
        call_command('rebuild_index', verbosity=0, interactive=False)

    def clear_index(self):
        call_command('clear_index', verbosity=0, interactive=False)
