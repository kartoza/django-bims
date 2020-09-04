# noinspection PyUnresolvedReferences,PyPackageRequirements
import factory
from bims_theme.models import (
    CarouselHeader,
    Partner,
    CustomTheme
)


class CarouselHeaderF(factory.django.DjangoModelFactory):
    """
    Carousel header model factory
    """

    class Meta:
        model = CarouselHeader

    title = factory.Sequence(lambda n: 'title_{}'.format(n))
    description = factory.Sequence(lambda n: 'description_{}'.format(n))
    banner = factory.django.FileField(filename='banner.png')


class PartnerF(factory.django.DjangoModelFactory):
    """
    Partner model factory
    """
    class Meta:
        model = Partner

    name = factory.Sequence(lambda n: 'partner_{}'.format(n))
    logo = factory.django.FileField(filename='logo.png')


class CustomThemeF(factory.django.DjangoModelFactory):
    """
    Custom theme factory
    """
    class Meta:
        model = CustomTheme

    name = factory.Sequence(lambda n: 'name_{}'.format(n))
    description = factory.Sequence(lambda n: 'description_{}'.format(n))
    site_name = factory.Sequence(lambda n: 'site_name_{}'.format(n))

    @factory.post_generation
    def partners(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for partner in extracted:
                self.partners.add(partner)

    @factory.post_generation
    def carousels(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for carousel in extracted:
                self.carousels.add(carousel)
