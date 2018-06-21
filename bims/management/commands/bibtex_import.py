# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand, CommandError

from td_biblio.utils.loaders import BibTeXLoader


class Command(BaseCommand):
    help = "Import entries from a BibTex file"

    def _get_logger(self):
        logger = logging.getLogger('td_biblio')
        return logger

    def add_arguments(self, parser):
        parser.add_argument(
            'bibtex',
            help="The path to the BibTeX file to import"
        )

    def handle(self, *args, **options):
        logger = self._get_logger()

        bibtex = options.get('bibtex', None)
        if bibtex is None:
            raise CommandError("A BibTeX file path is required")

        logger.info("Importing '{}' BibTeX file...".format(bibtex))
        loader = BibTeXLoader()
        loader.load_records(bibtex_filename=bibtex)
        loader.save_records()
        logger.info("Importation succeeded")
