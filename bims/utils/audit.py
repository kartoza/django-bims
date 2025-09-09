from contextlib import contextmanager
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.conf import settings


def easy_audit_callback(
        instance,
        object_json_repr,
        created,
        raw,
        using,
        update_fields,
        **kwargs) -> bool:
    from easyaudit.utils import model_delta
    from django.core.exceptions import ObjectDoesNotExist

    if created:
        return True

    model_class = instance.__class__
    try:
        old_model = model_class.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        return False
    delta = model_delta(old_model, instance)
    all_changes = []

    if delta:
        for field, changes in delta.items():
            old_value, new_value = changes
            if old_value == 'None' and new_value == '':
                all_changes.append(False)
                continue
            if field == 'hierarchical_data':
                all_changes.append(False)
                continue
            all_changes.append(True)

    return any(all_changes)



def _get_easyaudit_handlers():
    from easyaudit.signals import model_signals
    return [
        (pre_save,   model_signals.pre_save),
        (post_save,  model_signals.post_save),
        (m2m_changed, model_signals.m2m_changed),
    ]


@contextmanager
def disable_easy_audit():
    if not 'easyaudit' in settings.INSTALLED_APPS:
        yield
    disconnected = []
    for sig, handler in _get_easyaudit_handlers():
        try:
            sig.disconnect(handler)
            disconnected.append((sig, handler))
        except Exception:
            pass
    try:
        yield
    finally:
        for sig, handler in disconnected:
            try:
                sig.connect(handler)
            except Exception:
                pass
