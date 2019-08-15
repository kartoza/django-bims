# noinspection PyUnresolvedReferences,PyPackageRequirements
import factory
from td_biblio.models.bibliography import (
    Author, Entry, Journal)


class AuthorF(factory.django.DjangoModelFactory):
    """
    Author status factory
    """

    class Meta:
        model = Author

    first_name = factory.Sequence(lambda n: 'First name %s' % n)
    last_name = factory.Sequence(lambda n: 'Last name %s' % n)


class JournalF(factory.django.DjangoModelFactory):
    """
    Journal status factory
    """

    class Meta:
        model = Journal

    name = factory.Sequence(lambda n: 'name %s' % n)


class EntryF(factory.django.DjangoModelFactory):
    """
    Entry status factory
    """

    class Meta:
        model = Entry

    type = Entry.ARTICLE
    title = factory.Sequence(lambda n: 'Title %s' % n)
