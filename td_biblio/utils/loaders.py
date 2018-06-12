# -*- coding: utf-8 -*-
"""
Bibliography Manager Tools
"""
from __future__ import unicode_literals

import datetime
import json
import logging
import sys

import bibtexparser
import eutils.client

from time import strptime

from bibtexparser import customization as bp_customization
from bibtexparser.bparser import BibTexParser
from bibtexparser.latexenc import string_to_latex
from django.utils.translation import ugettext_lazy as _
from habanero import cn

from ..exceptions import DOILoaderError, PMIDLoaderError
from ..models import Author, Journal, Entry, AuthorEntryRank


logger = logging.getLogger('td_biblio')


def to_latex(record):
    """
    Convert strings to latex
    """
    for val in record:
        record[val] = string_to_latex(record[val])
    return record


def td_biblio_customization(record):
    """
    Customize BibTex records parsing
    """
    # Convert crapy things to latex
    record = to_latex(record)
    # and then to unicode
    record = bp_customization.convert_to_unicode(record)
    record = bp_customization.type(record)
    record = bp_customization.author(record)
    record = bp_customization.editor(record)
    record = bp_customization.page_double_hyphen(record)

    return record


class BaseLoader(object):

    def __init__(self):
        self.entry_base_fields = (
            'type', 'title', 'volume', 'number', 'pages', 'url',
            'publication_date', 'is_partial_publication_date'
        )
        self.records = []

    def to_record(self, input):
        """Convert an item to import to a valid record

        valid_record = {
            'title': 'A coarse-grained protein force field …',
            'authors': [
                {
                    'first_name': 'Julien',
                    'last_name': 'Maupetit'
                },
                {
                    'first_name': 'P',
                    'last_name': 'Tuffery'
                },
                {
                    'first_name': 'Philippe',
                    'last_name': 'Derreumaux'
                }
            ],
            'journal': 'Proteins: Structure, Function, and Bioinformatics',
            'volume': '69',
            'number': '2',
            'pages': '394--408',
            'year': '2007',
            'publisher': 'Wiley Online Library',
            'ENTRYTYPE': 'article',
            'ID': 'maupetit2007coarse',
            'publication_date': datetime.date(2007, 1, 1),
            'is_partial_publication_date': True
        }
        """
        raise NotImplemented(
            _(
                "You should implement a to_record method for {}".format(
                    self.__class__.__name__
                )
            )
        )

    def load_records(self, **kwargs):
        """Load all records in self.records"""

        raise NotImplemented(
            _(
                "You should implement a load_records method for {}".format(
                    self.__class__.__name__
                )
            )
        )

    def save_record(self, record):
        """Save a single record"""

        logger.debug("Record: {}".format(record))

        entry_fields = dict(
            (k, v) for (k, v) in record.items() if k in self.entry_base_fields
        )

        # Foreign keys
        journal, is_new = Journal.objects.get_or_create(
            name=record['journal']
        )
        entry_fields['journal'] = journal
        logger.debug("Journal: {}".format(journal))

        # Save or Update this entry
        entry, is_new = Entry.objects.get_or_create(**entry_fields)

        # Authors
        for rank, record_author in enumerate(record['authors']):
            author, _ = Author.objects.get_or_create(
                first_name=record_author['first_name'],
                last_name=record_author['last_name'],
            )

            AuthorEntryRank.objects.get_or_create(
                entry=entry,
                author=author,
                rank=rank,
            )
        logger.debug("(New) Entry imported with success: {}".format(entry))

    def save_records(self):
        """Batch save records"""
        for record in self.records:
            self.save_record(record)


class BibTeXLoader(BaseLoader):
    """BibTeXLoader

    This loader is designed to import a bibtex file items.

    Usage:

    >>> from td_biblio.utils.loaders import BibTeXLoader
    >>> loader = BibTeXLoader()
    >>> loader.load_records(bibtex_filename='foo.bib')
    >>> loader.save_records()
    """

    def to_record(self, input):
        """Convert a bibtex item to a valid record"""

        # Simple fields
        record = input.copy()

        # Journal
        record['journal'] = input['journal']

        # Publication date
        pub_date = {'day': 1, 'month': 1, 'year': 1900}
        input_date = dict(
            (k, v) for (k, v) in input.items() if k in pub_date.keys()
        )
        pub_date.update(input_date)
        # Check if month is numerical or not
        try:
            int(pub_date['month'])
        except ValueError:
            pub_date['month'] = strptime(pub_date['month'], '%b').tm_mon
        # Convert date fields to integers
        pub_date = dict(
            (k, int(v)) for k, v in pub_date.items()
        )
        record['publication_date'] = datetime.date(**pub_date)

        record['is_partial_publication_date'] = not all(
            [True if k in input else False for k in pub_date.keys()]
        )

        # Authors
        record['authors'] = []
        for author in input['author']:
            splited = author.split(', ')
            record['authors'].append(
                {
                    'first_name': " ".join(splited[1:]),
                    'last_name': splited[0],
                }
            )
        return record

    def load_records(self, bibtex_filename=None):
        """Load all bibtex items as valid records"""

        with open(bibtex_filename) as bibtex_file:
            # Parse BibTex file
            parser = BibTexParser()
            parser.customization = td_biblio_customization
            bp = bibtexparser.load(bibtex_file, parser=parser)
            self.records = [self.to_record(r) for r in bp.get_entry_list()]


class PubmedLoader(BaseLoader):
    """PubmedLoader

    This loader is designed to fetch & import a list of Pubmed IDs

    Usage:

    >>> from td_biblio.utils.loaders import PubmedLoader
    >>> loader = PubmedLoader()
    >>> loader.load_records(PMIDs=26588162)
    >>> loader.save_records()
    """

    def __init__(self, *args, **kwargs):
        super(PubmedLoader, self).__init__(*args, **kwargs)
        self.client = eutils.client.Client()

    def to_record(self, input):
        """Convert eutils PubmedArticle xml facade to a valid record"""

        record = {
            'title': input.title,
            'authors': [],
            'journal': input.jrnl,
            'volume': input.volume,
            'number': input.issue if input.issue is not None else '',
            'pages': input.pages,
            'year': input.year,
            'publication_date': datetime.date(int(input.year), 1, 1),
            'is_partial_publication_date': True
        }

        for author in input.authors:
            splited = author.split()
            record['authors'].append(
                {
                    'first_name': " ".join(splited[1:]),
                    'last_name': splited[0],
                }
            )

        return record

    def load_records(self, PMIDs=None):
        """Load all PMIDs as valid records"""

        entries = self.client.efetch(db='pubmed', id=PMIDs)
        self.records = []

        for entry in entries:
            try:
                record = self.to_record(entry)
            except Exception:
                e, v, tb = sys.exc_info()
                msg = _(
                    "An error occured while loading the following PMID: {}. "
                    "Check logs for details."
                ).format(
                    entry.pmid
                )
                logger.error(
                    '{}, error: {} [{}], data: {}'.format(msg, e, v, entry)
                )
                raise PMIDLoaderError(msg)
            self.records.append(record)


class DOILoader(BaseLoader):
    """DOILoader

    This loader is designed to fetch & import a list of DOIs

    Usage:

    >>> from td_biblio.utils.loaders import DOILoader
    >>> loader = DOILoader()
    >>> loader.load_records(DOIs='10.1021/ct500592m')
    >>> loader.save_records()
    """

    def to_record(self, input):
        """Convert crossref item to a valid record"""

        date_parts = input['issued']['date-parts'][0]
        is_partial_publication_date = len(date_parts) != 3

        # Fill date parts if only a year is given
        if is_partial_publication_date:
            date_parts = date_parts + ((3 - len(date_parts)) * [1])

        # Journal name defaults to 'short-container-title'
        # It falls back to 'container-title'
        if input.get('short-container-title'):
            journal = input['short-container-title'][0]
        else:
            journal = input.get('container-title', '')

        record = {
            'title': input.get('title', ''),
            'authors': [
                {
                    'first_name': a.get('given', ''),
                    'last_name': a.get('family', '')
                } for a in input.get('author')
            ],
            'journal': journal,
            'volume': input.get('volume', ''),
            'number': input.get('issue', ''),
            'pages': input.get('page', ''),
            'year': date_parts[0],
            'publication_date': datetime.date(*date_parts),
            'is_partial_publication_date': is_partial_publication_date
        }

        return record

    def load_records(self, DOIs=None):
        """Load all crossref items as valid records"""

        records = cn.content_negotiation(ids=DOIs, format='citeproc-json')
        # Records might be a str or unicode (python 2)
        if not isinstance(records, list):
            records = [records, ]
        self.records = []
        for r in records:
            data = json.loads(r)
            try:
                record = self.to_record(data)
            except Exception:
                e, v, tb = sys.exc_info()
                msg = _(
                    "An error occured while loading the following DOI: {}. "
                    "Check logs for details."
                ).format(
                    data.get('DOI')
                )
                logger.error(
                    '{}, error: {} [{}], data: {}'.format(msg, e, v, data)
                )
                raise DOILoaderError(msg)
            self.records.append(record)
