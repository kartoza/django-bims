from django.apps import AppConfig
from django.db.models import signals


class BimsAppConfig(AppConfig):
    name = 'bims'

    def ready(self):
        from easyaudit.signals.model_signals import m2m_changed
        is_ready = True
        def easy_audit_m2m_changed(sender, instance, action, reverse, model, pk_set, using, **kwargs):
            if len(list(pk_set)) == 0:
                return
            return m2m_changed(
                sender,
                instance,
                action,
                reverse,
                model,
                pk_set,
                using,
                **kwargs
            )

        signals.m2m_changed.disconnect(dispatch_uid='easy_audit_signals_m2m_changed')
        signals.m2m_changed.connect(easy_audit_m2m_changed, dispatch_uid='easy_audit_signals_m2m_changed')
