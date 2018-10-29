from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

class SignalsConfig(AppConfig):
    name = 'bims.signals'
    verbose_name = _('signals')

    def ready(self):
        import bims.signals.group_profile  # noqa
