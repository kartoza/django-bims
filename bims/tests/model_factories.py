# noinspection PyUnresolvedReferences,PyPackageRequirements
import factory
import random
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.db.models import signals
from bims.models import (
    LocationType,
    LocationSite,
    Profile,
    IUCNStatus,
    Taxon,
    Survey,
    LocationContext,
    BiologicalCollectionRecord,
)


class LocationContextF(factory.django.DjangoModelFactory):
    """
    Location context factory
    """
    class Meta:
        model = LocationContext

    context_document = '{"type": "FeatureCollection", "features":' \
                       ' [{"type": "Feature","properties": {},' \
                       '"geometry": {"type": "Point",' \
                       '"coordinates": [20.654296875,-33.275435412981615]}}]}'


class LocationTypeF(factory.django.DjangoModelFactory):
    """
    Location type factory
    """

    class Meta:
        model = LocationType

    name = factory.Sequence(lambda n: 'Test location type %s' % n)
    description = u'Only for testing'
    allowed_geometry = 'POINT'


class LocationSiteF(factory.django.DjangoModelFactory):
    """
    Location site factory
    """

    class Meta:
        model = LocationSite

    location_type = factory.SubFactory(LocationTypeF)
    geometry_point = Point(
        random.uniform(-180.0, 180.0),
        random.uniform(-90.0, 90.0)
    )
    location_context = factory.SubFactory(LocationContextF)


class ProfileF(factory.django.DjangoModelFactory):
    """
    Profile site factory
    """

    class Meta:
        model = Profile

    user = factory.SubFactory(User)
    qualifications = factory.Sequence(lambda n: "qualifications%s" % n)
    other = factory.Sequence(lambda n: "other%s" % n)


class IUCNStatusF(factory.django.DjangoModelFactory):
    """
    Iucn status factory
    """
    class Meta:
        model = IUCNStatus

    category = factory.Sequence(lambda n: u'Test name %s' % n)
    sensitive = False


@factory.django.mute_signals(signals.pre_save)
class TaxonF(factory.django.DjangoModelFactory):
    """
    Taxon factory
    """
    class Meta:
        model = Taxon

    iucn_status = factory.SubFactory(IUCNStatusF)
    common_name = factory.Sequence(lambda n: u'Test common name %s' % n)
    scientific_name = factory.Sequence(
            lambda n: u'Test scientific name %s' % n)
    author = factory.Sequence(lambda n: u'Test author %s' % n)


class SurveyF(factory.django.DjangoModelFactory):
    """
    Survey factory
    """
    class Meta:
        model = Survey

    date = timezone.now()

    @factory.post_generation
    def sites(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for site in extracted:
                self.sites.add(site)


class UserF(factory.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "username%s" % n)
    first_name = factory.Sequence(lambda n: "first_name%s" % n)
    last_name = factory.Sequence(lambda n: "last_name%s" % n)
    email = factory.Sequence(lambda n: "email%s@example.com" % n)
    password = ''
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
    taxon_gbif_id = factory.SubFactory(TaxonF)
