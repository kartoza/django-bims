from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from rest_framework import serializers

from bims.models import TaxonGroupTaxonomy
from bims.models.taxonomy import Taxonomy
from bims.scripts.collection_csv_keys import PARK_OR_MPA_NAME
from bims.serializers.bio_collection_serializer import SerializerContextCache
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.dataset import Dataset


def get_dataset_occurrences(occurrences):
    dataset_keys = list(occurrences.values_list(
        'additional_data__datasetKey',
        flat=True
    ))
    if dataset_keys:
        dataset_keys = list(filter(None, set(dataset_keys)))
        datasets = Dataset.objects.filter(
            uuid__in=dataset_keys
        )
        dataset_names = []
        if datasets.exists():
            for dataset in datasets:
                dataset_names.append(
                    dataset.abbreviation if dataset.abbreviation else dataset.name
                )
                dataset_keys.remove(str(dataset.uuid))
        if dataset_keys:
            dataset_names.extend(dataset_keys)
        if len(dataset_names) > 0:
            return list(set(dataset_names))
    dataset_names = list(occurrences.values_list(
        'additional_data__datasetName',
        flat=True
    ))
    dataset_names = [name for name in dataset_names if name is not None]
    if dataset_names:
        return list(set(dataset_names))
    return []


class ChecklistBaseSerializer(SerializerContextCache):
    def get_bio_data(self, obj: Taxonomy):
        if not hasattr(self, '_bio_data_cache'):
            self._bio_data_cache = {}
        bio_context = self.context.get(
            'collection_records', BiologicalCollectionRecord.objects.all())
        if obj.id not in self._bio_data_cache:
            bio_records = bio_context.filter(taxonomy=obj)
            self._bio_data_cache[obj.id] = bio_records
        return self._bio_data_cache[obj.id]

    def clean_text(self, text):
        if text is None:
            return ''
        # Remove or replace unwanted characters
        cleaned_text = text.replace('\n', ' ').replace('\r', ' ')
        return cleaned_text

    def get_sources(self, obj: Taxonomy):
        bio = self.get_bio_data(obj)
        if not bio.exists():
            return ''
        sources = []
        if bio.filter(source_collection__iexact='gbif').exists():
            sources = get_dataset_occurrences(bio)
        bio = bio.distinct('source_reference')
        try:
            for collection in bio:
                try:
                    if (
                        collection.source_reference and
                        str(collection.source_reference) != 'Global Biodiversity Information Facility (GBIF)'
                    ):
                        if collection.additional_data and 'Citation' in collection.additional_data:
                            citation_name = collection.additional_data['Citation']
                            if not Dataset.objects.filter(citation=citation_name).exists():
                                Dataset.objects.create(
                                    citation=citation_name,
                                    abbreviation=citation_name,
                                    name=str(collection.source_reference)
                                )
                            else:
                                dataset = Dataset.objects.filter(citation=citation_name).first()
                                if dataset.abbreviation != citation_name:
                                    citation_name = dataset.abbreviation
                            sources.append(
                                citation_name
                            )
                        else:
                            sources.append(
                                str(collection.source_reference)
                            )
                except ContentType.DoesNotExist:
                    continue
        except TypeError:
            pass
        if sources:
            return ', '.join(set(filter(None, sources)))
        return '-'


class ChecklistPDFSerializer(ChecklistBaseSerializer):

    common_name = serializers.SerializerMethodField()
    threat_status = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    scientific_name = serializers.SerializerMethodField()
    occurrence_records = serializers.SerializerMethodField()

    def get_occurrence_records(self, obj: Taxonomy):
        bio = self.get_bio_data(obj)
        if not bio.exists():
            return 0
        return bio.count()

    def get_scientific_name(self, obj: Taxonomy):
        return self.clean_text(obj.scientific_name)

    def get_common_name(self, obj: Taxonomy):
        vernacular_names = list(
            obj.vernacular_names.filter(
                language__istartswith='en'
            ).values_list('name', flat=True))
        if len(vernacular_names) == 0:
            return ''
        else:
            return vernacular_names[0]

    def get_threat_status(self, obj: Taxonomy):
        if obj.iucn_status:
            return obj.iucn_status.category
        return 'NE'

    class Meta:
        model = Taxonomy
        fields = [
            'id',
            'scientific_name',
            'common_name',
            'threat_status',
            'sources',
            'occurrence_records'
        ]



class ChecklistSerializer(ChecklistBaseSerializer):
    """
    Serializer for checklist
    """
    kingdom = serializers.SerializerMethodField()
    phylum = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    synonyms = serializers.SerializerMethodField()
    common_name = serializers.SerializerMethodField()
    most_recent_record = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    invasion = serializers.SerializerMethodField()
    endemism = serializers.SerializerMethodField()
    global_conservation_status = serializers.SerializerMethodField()
    national_conservation_status = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    cites_listing = serializers.SerializerMethodField()
    confidence = serializers.SerializerMethodField()
    park_or_mpa_name = serializers.SerializerMethodField()
    creation_date = serializers.SerializerMethodField()
    occurrence_records = serializers.SerializerMethodField()

    def taxon_name_by_rank(
            self,
            obj: Taxonomy,
            rank_identifier: str):
        taxon_name = self.get_context_cache(
            rank_identifier,
            obj.id
        )
        if taxon_name:
            return taxon_name
        taxon_name = obj.__getattribute__(rank_identifier)
        if taxon_name:
            self.set_context_cache(
                rank_identifier,
                obj.id,
                taxon_name
            )
            return taxon_name
        return '-'

    def get_creation_date(self, obj: Taxonomy):
        today = datetime.today()
        return today.strftime('%d/%m/%Y')

    def get_taxon_group_taxon_data(self, obj: Taxonomy):
        taxon_group_id = self.context.get('taxon_group_id', None)
        if not taxon_group_id:
            return None
        if not hasattr(self, '_taxon_group_cache'):
            self._taxon_group_cache = {}
        if obj.id not in self._taxon_group_cache:
            taxon_group_taxon = TaxonGroupTaxonomy.objects.filter(
                taxonomy=obj,
                taxongroup_id=taxon_group_id,
                is_validated=True
            ).first()
            if taxon_group_taxon:
                self._taxon_group_cache[obj.id] = taxon_group_taxon
            else:
                return None
        return self._taxon_group_cache[obj.id]

    def get_kingdom(self, obj: Taxonomy):
        return self.taxon_name_by_rank(
            obj,
            'kingdom_name'
        )
    def get_class_name(self, obj):
        return self.taxon_name_by_rank(
            obj,
            'class_name'
        )

    def get_phylum(self, obj):
        return self.taxon_name_by_rank(
            obj,
            'phylum_name'
        )

    def get_order(self, obj):
        return self.taxon_name_by_rank(
            obj,
            'order_name'
        )

    def get_family(self, obj):
        return self.taxon_name_by_rank(
            obj,
            'family_name'
        )

    def get_synonyms(self, obj: Taxonomy):
        synonyms = Taxonomy.objects.filter(
            accepted_taxonomy=obj
        ).values_list('scientific_name', flat=True)
        return ','.join(list(synonyms))

    def get_common_name(self, obj: Taxonomy):
        vernacular_names = list(
            obj.vernacular_names.filter(
                language__istartswith='en').values_list('name', flat=True))
        if len(vernacular_names) == 0:
            return ''
        else:
            return vernacular_names[0]

    def get_most_recent_record(self, obj: Taxonomy):
        bio = self.get_bio_data(obj)
        if not bio.exists():
            return ''
        return bio.order_by('collection_date').last().collection_date.year

    def get_occurrence_records(self, obj: Taxonomy):
        bio = self.get_bio_data(obj)
        if not bio.exists():
            return 0
        return bio.count()

    def get_confidence(self, obj: Taxonomy):
        bio = self.get_bio_data(obj)
        if not bio.exists():
            return ''
        if bio.exclude(certainty_of_identification='').exists():
            return (
                bio.exclude(
                    certainty_of_identification=''
                ).first().certainty_of_identification
            )
        return ''

    def get_park_or_mpa_name(self, obj: Taxonomy):
        bio = self.get_bio_data(obj)
        if not bio.exists():
            return '-'
        if bio.exclude(source_collection__iexact='gbif').exists():
            park_names = list(bio.annotate(
                    park_name=F(f'additional_data__{PARK_OR_MPA_NAME}')
                ).values_list('park_name', flat=True)
            )
            park_names = [name for name in park_names if name is not None]
            if park_names:
                return ','.join(set(park_names))
        return '-'

    def get_origin(self, obj: Taxonomy):
        origin_categories = dict(Taxonomy.CATEGORY_CHOICES)
        taxon_group_taxon = self.get_taxon_group_taxon_data(obj)
        if not taxon_group_taxon:
            taxon_group_taxon = obj
        return (
            origin_categories[taxon_group_taxon.origin]
            if taxon_group_taxon.origin in origin_categories
            else ''
        )

    def get_invasion(self, obj: Taxonomy):
        if obj.invasion:
            return obj.invasion.category
        return ''

    def get_endemism(self, obj: Taxonomy):
        taxon_group_taxon = self.get_taxon_group_taxon_data(obj)
        if not taxon_group_taxon:
            taxon_group_taxon = obj
        return taxon_group_taxon.endemism.name if taxon_group_taxon.endemism else ''

    def get_global_conservation_status(self, obj):
        if obj.iucn_status:
            return obj.iucn_status.category
        return 'NE'

    def get_national_conservation_status(self, obj):
        if obj.national_conservation_status:
            return obj.national_conservation_status.category
        return ''

    def get_cites_listing(self, obj: Taxonomy):
        return obj.cites_listing

    class Meta:
        model = Taxonomy
        fields = [
            'id',
            'kingdom',
            'phylum',
            'class_name',
            'order',
            'family',
            'scientific_name',
            'synonyms',
            'rank',
            'common_name',
            'most_recent_record',
            'origin',
            'invasion',
            'endemism',
            'global_conservation_status',
            'national_conservation_status',
            'sources',
            'cites_listing',
            'confidence',
            'park_or_mpa_name',
            'creation_date',
            'occurrence_records'
        ]
