# noinspection PyUnresolvedReferences,PyPackageRequirements
import factory
import random
from django.conf import settings
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.db.models import signals
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from bims.models import (
    LocationType,
    LocationSite,
    Profile,
    IUCNStatus,
    Survey,
    BiologicalCollectionRecord,
    Boundary,
    BoundaryType,
    Cluster,
    Endemism,
    Taxonomy,
    TaxonGroup,
    FbisUUID,
    DataSource,
    Biotope,
    SourceReference,
    SourceReferenceBibliography,
    SourceReferenceDatabase,
    DatabaseRecord,
    LocationContext,
    LocationContextGroup,
)


class LocationTypeF(factory.django.DjangoModelFactory):
    """
    Location type factory
    """

    class Meta:
        model = LocationType
        django_get_or_create = ('id', )

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'Test location type %s' % n)
    description = u'Only for testing'
    allowed_geometry = 'POINT'


@factory.django.mute_signals(signals.post_save)
class LocationSiteF(factory.django.DjangoModelFactory):
    """
    Location site factory
    """

    class Meta:
        model = LocationSite
        django_get_or_create = ('id', )

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'Site name %s' % n)
    location_type = factory.SubFactory(LocationTypeF)
    geometry_point = Point(
        random.uniform(-30.0, 30.0),
        random.uniform(-30.0, 30.0)
    )


class LocationContextGroupF(factory.django.DjangoModelFactory):
    """
    Location context group factory
    """
    class Meta:
        model = LocationContextGroup

    name = factory.Sequence(lambda n: 'name %s' % n)
    key = factory.Sequence(lambda n: 'key %s' % n)
    geocontext_group_key = factory.Sequence(lambda n: 'group_key %s' % n)
    layer_name = factory.Sequence(lambda n: 'layer_name %s' % n)


class LocationContextF(factory.django.DjangoModelFactory):
    """
    Location context factory
    """
    class Meta:
        model = LocationContext

    site = factory.SubFactory(LocationSiteF)
    group = factory.SubFactory(LocationContextGroupF)
    value = factory.Sequence(lambda n: 'value %s' % n)


class IUCNStatusF(factory.django.DjangoModelFactory):
    """
    Iucn status factory
    """
    class Meta:
        model = IUCNStatus

    category = factory.Sequence(lambda n: u'Test name %s' % n)
    sensitive = False


class SurveyF(factory.django.DjangoModelFactory):
    """
    Survey factory
    """
    class Meta:
        model = Survey

    date = timezone.now()
    site = factory.SubFactory(LocationSiteF)


class EndemismF(factory.django.DjangoModelFactory):
    """
    Endemism factory
    """
    class Meta:
        model = Endemism

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'name %s' % n)
    description = factory.Sequence(
        lambda n: 'description %s' % n
    )


class GroupF(factory.DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: 'group %s' % n)


class ContentTypeF(factory.DjangoModelFactory):
    class Meta:
        model = ContentType

    app_label = factory.Sequence(lambda n: 'app %s' % n)
    model = factory.Sequence(lambda n: 'model %s' % n)


class PermissionF(factory.DjangoModelFactory):
    class Meta:
        model = Permission

    name = factory.Sequence(lambda n: 'permission %s' % n)
    content_type = factory.SubFactory(ContentTypeF)


class UserF(factory.DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL
        django_get_or_create = ('id', )

    id = factory.Sequence(lambda n: n)
    username = factory.Sequence(lambda n: "username%s" % n)
    first_name = factory.Sequence(lambda n: "first_name%s" % n)
    last_name = factory.Sequence(lambda n: "last_name%s" % n)
    email = factory.Sequence(lambda n: "email%s@example.com" % n)
    password = factory.PostGenerationMethodCall('set_password', 'password')
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = timezone.datetime(2000, 1, 1).replace(tzinfo=timezone.utc)
    date_joined = timezone.datetime(1999, 1, 1).replace(
        tzinfo=timezone.utc)

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserF, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user


class ProfileF(factory.django.DjangoModelFactory):
    """
    Profile site factory
    """

    class Meta:
        model = Profile

    user = factory.SubFactory(UserF)
    qualifications = factory.Sequence(lambda n: "qualifications%s" % n)
    other = factory.Sequence(lambda n: "other%s" % n)


class TaxonomyF(factory.django.DjangoModelFactory):
    """
    Taxon identifier factory
    """
    class Meta:
        model = Taxonomy
        django_get_or_create = ('id',)

    id = factory.Sequence(lambda n: n)
    iucn_status = factory.SubFactory(IUCNStatusF)
    scientific_name = factory.Sequence(lambda n: u'Scientific name %s' % n)
    canonical_name = factory.Sequence(lambda n: u'Canonical name %s' % n)


class TaxonGroupF(factory.django.DjangoModelFactory):
    """
    Taxon group factory
    """
    class Meta:
        model = TaxonGroup

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: u'Name %s' % n)

    @factory.post_generation
    def taxonomies(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for taxonomy in extracted:
                self.taxonomies.add(taxonomy)


@factory.django.mute_signals(signals.post_save)
class BiologicalCollectionRecordF(factory.django.DjangoModelFactory):
    """
    Biological collection record factory
    """
    class Meta:
        model = BiologicalCollectionRecord

    site = factory.SubFactory(LocationSiteF)
    original_species_name = factory.Sequence(
            lambda n: u'Test original species name %s' % n)
    category = 'alien'
    present = True
    collection_date = timezone.now()
    collector = factory.Sequence(
            lambda n: u'Test collector %s' % n)
    owner = factory.SubFactory(UserF)
    notes = factory.Sequence(
            lambda n: u'Test notes %s' % n)
    taxonomy = factory.SubFactory(TaxonomyF)
    validated = True


class BoundaryTypeF(factory.django.DjangoModelFactory):
    """
    Boundary type factory
    """
    class Meta:
        model = BoundaryType

    name = factory.Sequence(lambda n: u'Test name %s' % n)


class BoundaryF(factory.django.DjangoModelFactory):
    """
    Boundary factory
    """
    class Meta:
        model = Boundary

    name = factory.Sequence(lambda n: u'Test name %s' % n)
    type = factory.SubFactory(BoundaryTypeF)


class ClusterF(factory.django.DjangoModelFactory):
    """
    Cluster factory
    """
    class Meta:
        model = Cluster

    boundary = factory.SubFactory(BoundaryF)
    module = factory.Sequence(lambda n: u'Test module %s' % n)
    site_count = 1
    details = ''


class FbisUUIDF(factory.django.DjangoModelFactory):
    """
    FbisUUID factory
    """
    class Meta:
        model = FbisUUID

    id = factory.Sequence(lambda n: n)
    uuid = factory.Sequence(lambda n: 'uuid %s' % n)
    content_type = factory.SubFactory(ContentTypeF)


class DataSourceF(factory.django.DjangoModelFactory):
    """
    Data source factory
    """
    class Meta:
        model = DataSource

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'data-source %s' % n)


class BiotopeF(factory.django.DjangoModelFactory):
    class Meta:
        model = Biotope


class SourceReferenceF(factory.django.DjangoModelFactory):
    class Meta:
        model = SourceReference


class SourceReferenceBibliographyF(factory.django.DjangoModelFactory):
    class Meta:
        model = SourceReferenceBibliography


class SourceReferenceDatabaseF(factory.django.DjangoModelFactory):
    class Meta:
        model = SourceReferenceDatabase


class DatabaseRecordF(factory.django.DjangoModelFactory):
    class Meta:
        model = DatabaseRecord
