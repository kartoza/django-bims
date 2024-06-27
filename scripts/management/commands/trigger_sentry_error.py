from django.core.management.base import BaseCommand
from easyaudit.signals import model_signals

def trigger_error():
    raise Exception("easyaudit.signals.model_signals.pre_save test error")


class Command(BaseCommand):
    help = 'Trigger a test error to check Sentry configuration'

    def handle(self, *args, **kwargs):
        trigger_error()
