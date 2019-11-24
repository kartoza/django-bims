from functools import wraps


def prevent_recursion(func):
    # Prevent recursion for post_save signals

    @wraps(func)
    def no_recursion(sender, instance=None, **kwargs):
        if not instance:
            return
        if hasattr(instance, '_dirty'):
            return
        func(sender, instance=instance, **kwargs)
        try:
            instance._dirty = True
            instance.save()
        finally:
            del instance._dirty

    return no_recursion
