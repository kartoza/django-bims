# -*- coding: utf-8 -*-
import datetime
import factory
import random

from factory.django import DjangoModelFactory
from factory.fuzzy import BaseFuzzyAttribute

from . import models


JOURNAL_CHOICES = [
    (
        'Bioinformatics',
        'Bioinformatics'
    ),
    (
        'BMC Bioinf.',
        'BMC Bioinformatics'
    ),
    (
        'JACS',
        'Journal of the American Chemical Society'
    ),
    (
        'J. Comput. Chem.',
        'Journal of Computational Chemistry'
    ),
    (
        'Nat. Biotechnol.',
        'Nature Biotechnology'
    ),
    (
        'Nucleic Acids Res.',
        'Nucleic Acids Research'
    ),
    (
        'PNAS',
        'Proceedings of the National Academy of Sciences of the United '
        'States of America'
    ),
    (
        'Proteins Struct. Funct. Bioinf.',
        'Proteins: Structure, Function, and Bioinformatics'
    ),
]

ENTRY_TYPES_RAW_CHOICES = [c[0] for c in models.Entry.ENTRY_TYPES_CHOICES]


# Custom fuzzy attributes definition
#
class FuzzyPages(BaseFuzzyAttribute):
    """Random pages numbers separated by double-hyphens"""

    def __init__(self, low, high=None, **kwargs):
        if high is None:
            high = low
            low = 1

        self.low = low
        self.high = high

        super(FuzzyPages, self).__init__(**kwargs)

    def fuzz(self):
        start = random.randint(self.low, self.high)
        end = random.randint(start, self.high)
        return "%d--%d" % (start, end)


# Factories
#
class AbstractHumanFactory(DjangoModelFactory):

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

    class Meta:
            model = models.AbstractHuman
            abstract = True


class AuthorFactory(AbstractHumanFactory):

    class Meta:
        model = models.Author


class EditorFactory(AbstractHumanFactory):

    class Meta:
        model = models.Editor


class AbstractEntityFactory(DjangoModelFactory):

    class Meta:
        model = models.AbstractEntity
        abstract = True


class JournalFactory(AbstractEntityFactory):

    name = factory.Iterator(JOURNAL_CHOICES, getter=lambda c: c[1])
    abbreviation = factory.Iterator(JOURNAL_CHOICES, getter=lambda c: c[0])

    class Meta:
        model = models.Journal
        django_get_or_create = ('abbreviation', )


class PublisherFactory(AbstractEntityFactory):

    class Meta:
        model = models.Publisher


class EntryFactory(DjangoModelFactory):

    type = factory.fuzzy.FuzzyChoice(ENTRY_TYPES_RAW_CHOICES)
    title = factory.Sequence(lambda n: 'Entry title %s' % n)
    journal = factory.SubFactory(JournalFactory)
    publication_date = factory.fuzzy.FuzzyDate(datetime.date(1942, 1, 1))
    volume = factory.fuzzy.FuzzyInteger(1, 10)
    number = factory.fuzzy.FuzzyInteger(1, 50)
    pages = FuzzyPages(1, 2000)

    class Meta:
        model = models.Entry


class CollectionFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'Collection name %s' % n)
    short_description = factory.fuzzy.FuzzyText(length=42)

    class Meta:
        model = models.Collection

    # m2m
    @factory.post_generation
    def entries(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for entry in extracted:
                self.entries.add(entry)


class AuthorEntryRankFactory(DjangoModelFactory):

    author = factory.SubFactory(AuthorFactory)
    entry = factory.SubFactory(EntryFactory)
    rank = factory.Iterator(range(1, 4), cycle=True)

    class Meta:
        model = models.AuthorEntryRank


class EntryWithAuthorsFactory(EntryFactory):

    author1 = factory.RelatedFactory(AuthorEntryRankFactory, 'entry')
    author2 = factory.RelatedFactory(AuthorEntryRankFactory, 'entry')
    author3 = factory.RelatedFactory(AuthorEntryRankFactory, 'entry')


class EntryWithStaticAuthorsFactory(EntryFactory):
    """Fix two authors first and last names"""

    author1 = factory.RelatedFactory(
        AuthorEntryRankFactory,
        'entry',
        author__first_name='John',
        author__last_name='McClane',
        rank=1)

    author2 = factory.RelatedFactory(
        AuthorEntryRankFactory,
        'entry',
        author__first_name='Holly',
        author__last_name='Gennero',
        rank=2)
