from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


def _should_skip():
    """Return True when opensearch-py is not installed (e.g. during migrations)."""
    try:
        import opensearchpy  # noqa
        return False
    except ImportError:
        return True


def connect_opensearch_signals():
    from bims.models.biological_collection_record import BiologicalCollectionRecord

    @receiver(post_save, sender=BiologicalCollectionRecord, weak=False,
              dispatch_uid='bims_opensearch_post_save')
    def on_record_save(sender, instance, **kwargs):
        if _should_skip():
            return
        from django.db import connection
        from bims.tasks.opensearch_index import index_collection_record
        # Capture schema_name now, before the task executes asynchronously,
        # so the worker knows which tenant schema to query.
        index_collection_record.delay(instance.id, connection.schema_name)

    @receiver(post_delete, sender=BiologicalCollectionRecord, weak=False,
              dispatch_uid='bims_opensearch_post_delete')
    def on_record_delete(sender, instance, **kwargs):
        if _should_skip():
            return
        from django.db import connection
        from bims.tasks.opensearch_index import delete_collection_record_from_index
        delete_collection_record_from_index.delay(instance.id, connection.schema_name)
