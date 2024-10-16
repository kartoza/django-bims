import sys

from django.core.management import BaseCommand
from django.core.serializers import serialize, deserialize
from django.contrib.auth import get_user_model
from bims.models import *
from bims.signals.utils import disconnect_bims_signals, connect_bims_signals
from bims_theme.models import *
from sass.models import *

UserModel = get_user_model()

MAX_INDEX = 1000


def _migrate(model, data, new_tenant_schema, ignore=None, index=0):
    connection.set_schema('public')
    data_count = data.count()
    end_index = index + MAX_INDEX if data_count > index + MAX_INDEX else data_count
    serialized_data = serialize('json', data[index: end_index])

    connection.set_schema(new_tenant_schema)
    print(f'Migrating {data_count} {model} [{index}:{end_index}]')
    for obj in deserialize('json', serialized_data):
        model_object = obj.object
        if ignore:
            if getattr(model_object, ignore):
                setattr(model_object, ignore.replace('_id', ''), None)
        if not model.objects.filter(
                id=model_object.id
        ).exists():
            try:
                model_object.save()
            except Exception as e:
                print(f'Error : {e}')
    if data_count > index + MAX_INDEX:
        _migrate(
            model, data, new_tenant_schema, ignore, index + MAX_INDEX
        )


def migrate_rivers(location_sites, source_site, new_tenant_schema):
    rivers = River.objects.filter(
        id__in=location_sites.values('river')
    ).distinct()
    sys.stdout.write(
        f'Total rivers : {rivers.count()}\n'
    )
    sass_rivers = serialize('json', rivers)

    connection.set_schema(new_tenant_schema)
    sys.stdout.write('Migrating rivers\n')
    for obj in deserialize('json', sass_rivers):
        river = obj.object
        if not River.objects.filter(
            id=river.id
        ).exists():
            if river.owner_id:
                river.owner = None
            river.save()


def migrate_location_sites(source_site, new_tenant_schema):
    connection.set_schema('public')
    bio = BiologicalCollectionRecord.objects.filter(
        Q(source_site=source_site) | Q(additional_observation_sites=source_site),
        source_collection__iexact='gbif'
    )
    location_site = LocationSite.objects.filter(
        id__in=bio.values('site')
    ).distinct()

    sys.stdout.write(f'Total location sites to migrate : {location_site.count()}\n')
    sys.stdout.write(f'Total location sites without owner : {location_site.filter(owner__isnull=False).count()}\n')

    location_site_owner = UserModel.objects.filter(
        id__in=location_site.filter(owner__isnull=False).values('owner')
    )
    sys.stdout.write(
        f'Total owner : {location_site_owner.count()}\n'
    )

    owners = serialize('json', location_site_owner)
    users = serialize('json', Profile.objects.filter(
        user__in=location_site_owner
    ))
    sys.stdout.write(
        f'Total profile : {Profile.objects.filter(user__in=location_site_owner).count()}\n'
    )

    location_types = serialize(
        'json',
        LocationType.objects.all()
    )
    migrate_rivers(
        location_site,
        source_site,
        new_tenant_schema
    )
    connection.set_schema(new_tenant_schema)

    sys.stdout.write('Migrating owners\n')
    for obj in deserialize('json', owners):
        user = obj.object
        if not UserModel.objects.filter(
            id=user.id
        ).exists():
            user.save()
    for obj in deserialize('json', users):
        owner = obj.object
        if not Profile.objects.filter(
            id=owner.id
        ).exists():
            owner.save()

    sys.stdout.write('Migrating sites\n')
    for obj in deserialize('json', location_types):
        location_type = obj.object
        if not LocationType.objects.filter(
            id=location_type.id
        ).exists():
            location_type.save()

    sys.stdout.flush()

    connection.set_schema('public')
    location_sites = LocationSite.objects.filter(
        id__in=bio.values('site')
    ).distinct()
    _migrate(LocationSite, location_sites, new_tenant_schema, 'creator_id')


def migrate_taxonomies(source_site, new_tenant_schema):
    connection.set_schema('public')
    taxon_groups = TaxonGroup.objects.filter(
        site_id=source_site
    )
    taxonomies = Taxonomy.objects.all().order_by('id')
    iucn_status = IUCNStatus.objects.filter(
        id__in=list(taxonomies.values_list('iucn_status_id', flat=True))
    )

    _migrate(TaxonGroup, taxon_groups, new_tenant_schema)
    _migrate(IUCNStatus, iucn_status, new_tenant_schema)
    _migrate(Endemism, Endemism.objects.filter(
        id__in=list(taxonomies.values_list('endemism_id', flat=True).distinct())
    ), new_tenant_schema)
    _migrate(Taxonomy, taxonomies, new_tenant_schema, 'owner_id')
    _migrate(TaxonGroupTaxonomy, TaxonGroupTaxonomy.objects.filter(
        taxongroup__in=taxon_groups
    ), new_tenant_schema)


def migrate_survey(source_site, new_tenant_schema):
    _migrate(AbundanceType, AbundanceType.objects.all(), new_tenant_schema, 'specific_module_id')
    _migrate(SamplingMethod, SamplingMethod.objects.all(), new_tenant_schema)
    _migrate(SamplingEffortMeasure, SamplingEffortMeasure.objects.all(), new_tenant_schema, 'specific_module_id')
    _migrate(Hydroperiod, Hydroperiod.objects.all(), new_tenant_schema)
    _migrate(WetlandIndicatorStatus, WetlandIndicatorStatus.objects.all(), new_tenant_schema)
    _migrate(Biotope, Biotope.objects.all(), new_tenant_schema)
    _migrate(DatabaseRecord, DatabaseRecord.objects.filter(
        sourcereferencedatabase__active_sites=source_site
    ), new_tenant_schema)
    _migrate(SourceReference, SourceReference.objects.filter(
        active_sites=source_site
    ), new_tenant_schema)

    connection.set_schema('public')
    bio = BiologicalCollectionRecord.objects.filter(
        Q(source_site=source_site) | Q(additional_observation_sites=source_site),
        source_collection__iexact='gbif'
    )
    _migrate(UserModel, UserModel.objects.filter(
        id__in=bio.values('owner')
    ), new_tenant_schema)
    _migrate(UserModel, Profile.objects.filter(
        user__in=bio.values('owner')
    ), new_tenant_schema)
    _migrate(Survey, Survey.objects.filter(
        id__in=bio.values('survey')
    ).distinct(), new_tenant_schema)


def migrate_biological_collection_record(source_site, new_tenant_schema):
    connection.set_schema('public')
    bio = BiologicalCollectionRecord.objects.filter(
        Q(source_site=source_site) | Q(additional_observation_sites=source_site),
        source_collection__iexact='gbif'
    )
    _migrate(BiologicalCollectionRecord, bio, new_tenant_schema, 'collector_user')


def migrate_context(source_site, new_tenant_schema):
    connection.set_schema('public')
    bio = BiologicalCollectionRecord.objects.filter(
        Q(source_site=source_site) | Q(additional_observation_sites=source_site),
        source_collection__iexact='gbif'
    )
    sites = LocationSite.objects.filter(
        id__in=bio.values('site_id')
    )
    location_context = LocationContext.objects.filter(
        site__in=sites
    ).distinct()
    location_context_group = LocationContextGroup.objects.filter(
        id__in=location_context.values('group_id')
    ).distinct()
    location_filter = LocationContextFilter.objects.filter(site=source_site)
    group_order = LocationContextFilterGroupOrder.objects.filter(
        filter__in=location_filter
    )
    _migrate(LocationContextGroup, location_context_group, new_tenant_schema)
    _migrate(LocationContext, location_context, new_tenant_schema)
    _migrate(LocationContextFilter, location_filter, new_tenant_schema)
    _migrate(LocationContextFilter, group_order, new_tenant_schema)


def migrate_theme(source_site, new_tenant_schema):
    custom_theme = CustomTheme.objects.filter(
        site=source_site
    )
    partners = Partner.objects.filter(
        customtheme__in=custom_theme
    )
    landing_page_sections = LandingPageSection.objects.filter(
        customtheme__in=custom_theme
    )
    landing_page_section_content = LandingPageSectionContent.objects.filter(
        landingpagesection__in=landing_page_sections
    )
    _migrate(
        CustomTheme,
        custom_theme,
        new_tenant_schema
    )
    _migrate(
        Partner,
        partners,
        new_tenant_schema
    )
    _migrate(
        LandingPageSection,
        landing_page_sections,
        new_tenant_schema
    )
    _migrate(
        LandingPageSectionContent,
        landing_page_section_content,
        new_tenant_schema
    )
    _migrate(
        NonBiodiversityLayer,
        NonBiodiversityLayer.objects.filter(
            source_site=source_site
        ),
        new_tenant_schema
    )


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-ss',
            '--source_site',
            dest='source_site',
            default='1',)
        parser.add_argument(
            '-t',
            '--new_tenant',
            dest='new_tenant',
            default='sanpark',)
        parser.add_argument(
            '-m',
            '--migrate',
            dest='migrate'
        )

    def handle(self, *args, **options):
        disconnect_bims_signals()

        source_site = options.get('source_site', 1)
        new_tenant = options.get('new_tenant', 'sanpark')
        migrate = options.get('migrate', 'taxa')

        if migrate == 'taxa':
            migrate_taxonomies(source_site, new_tenant)
        if migrate == 'site':
            migrate_location_sites(source_site, new_tenant)
        if migrate == 'survey':
            migrate_survey(source_site, new_tenant)
        if migrate == 'bio':
            migrate_biological_collection_record(
                source_site,
                new_tenant
            )
        if migrate == 'context':
            migrate_context(
                source_site,
                new_tenant
            )
        if migrate == 'theme':
            migrate_theme(
                source_site,
                new_tenant
            )

        connect_bims_signals()

