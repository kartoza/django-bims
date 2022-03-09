# coding=utf-8
from django.db.models import signals

from bims.models.location_site import (
    location_site_post_save_handler,
    LocationSite
)

from bims.models.biological_collection_record import (
    collection_post_save_handler, BiologicalCollectionRecord
)
from bims.models.location_context_filter import LocationContextFilter
from bims.models.location_context_group import LocationContextGroup
from bims.models.location_context_filter_group_order import (
    location_context_post_save_handler, LocationContextFilterGroupOrder
)
from bims.models.source_reference import (
    source_reference_post_save_handler,
    SourceReference, SourceReferenceDatabase, SourceReferenceBibliography,
    SourceReferenceDocument
)


def disconnect_bims_signals():
    signals.post_save.disconnect(
        collection_post_save_handler,
        sender=BiologicalCollectionRecord
    )
    signals.post_save.disconnect(
        location_site_post_save_handler,
        sender=LocationSite
    )
    signals.post_save.disconnect(
        source_reference_post_save_handler,
        sender=SourceReference
    )
    signals.post_save.disconnect(
        source_reference_post_save_handler,
        sender=SourceReferenceDatabase
    )
    signals.post_save.disconnect(
        source_reference_post_save_handler,
        sender=SourceReferenceBibliography
    )
    signals.post_save.disconnect(
        source_reference_post_save_handler,
        sender=SourceReferenceDocument
    )
    signals.post_save.disconnect(
        location_context_post_save_handler,
        sender=LocationContextGroup
    )
    signals.post_save.disconnect(
        location_context_post_save_handler,
        sender=LocationContextFilter
    )
    signals.post_save.disconnect(
        location_context_post_save_handler,
        sender=LocationContextFilterGroupOrder
    )

def connect_bims_signals():
    signals.post_save.connect(
        collection_post_save_handler,
        sender=BiologicalCollectionRecord
    )
    signals.post_save.connect(
        location_site_post_save_handler,
        sender=LocationSite
    )
    signals.post_save.connect(
        source_reference_post_save_handler,
        sender=SourceReference
    )
    signals.post_save.connect(
        source_reference_post_save_handler,
        sender=SourceReferenceDatabase
    )
    signals.post_save.connect(
        source_reference_post_save_handler,
        sender=SourceReferenceBibliography
    )
    signals.post_save.connect(
        source_reference_post_save_handler,
        sender=SourceReferenceDocument
    )
    signals.post_save.connect(
        location_context_post_save_handler,
        sender=LocationContextGroup
    )
    signals.post_save.connect(
        location_context_post_save_handler,
        sender=LocationContextFilter
    )
    signals.post_save.connect(
        location_context_post_save_handler,
        sender=LocationContextFilterGroupOrder
    )
