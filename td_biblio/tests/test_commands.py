# -*- coding: utf-8 -*-
"""
TailorDev Bibliography

Test commands.
"""
from __future__ import unicode_literals

import os.path
import pytest

from django.core.management.base import CommandError
from django.test import TestCase

from ..management.commands import bibtex_import
from ..models import Author, Entry, Journal

FileNotFoundError = getattr(__builtins__, 'FileNotFoundError', IOError)


@pytest.mark.django_db
class BibTexImportCommandTests(TestCase):
    """
    Tests for the bibtex_import admin command
    """
    def setUp(self):
        """
        Set object level vars
        """
        self.bibtex_file = os.path.abspath(
            os.path.dirname(__file__) + '/fixtures/biblio.bib'
        )
        self.cmd = bibtex_import.Command()

    def test_command(self):
        """
        Test python manage.py bibtex_import biblio.bib
        """
        # Without an input file to handle, cmd shoud assert a CommandError
        with self.assertRaises(CommandError):
            self.cmd.handle()

        # Execute the command
        self.cmd.handle(bibtex=self.bibtex_file)

        # How many entries did we successfully import?
        self.assertEqual(Entry.objects.count(), 9)

        # How many journals?
        self.assertEqual(Journal.objects.count(), 5)

        # How many authors?
        self.assertEqual(Author.objects.count(), 31)

    def test_command_with_a_wrong_path(self):
        """Test command with a wrong path"""
        with self.assertRaises(FileNotFoundError):
            self.cmd.handle(bibtex='fake/path')
        self.assertEqual(Entry.objects.count(), 0)
