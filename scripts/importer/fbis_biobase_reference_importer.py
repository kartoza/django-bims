import re
from datetime import datetime
from scripts.importer.fbis_postgres_importer import FbisPostgresImporter
from td_biblio.models.bibliography import (
    Entry, Author, Journal, AuthorEntryRank
)
from bims.models.source_reference import SourceReferenceBibliography


class FbisBiobaseReferenceImporter(FbisPostgresImporter):

    table_name = 'public."BioReference"'
    content_type_model = SourceReferenceBibliography

    def parse_author(self, authors):
        author_list = []
        for author in authors:
            author = author.strip()
            if len(authors) > 1 or '&' in author:
                if '&' in author:
                    split_by = '&'
                else:
                    split_by = '. '
                _author_list = self.parse_author(author.split(split_by))
                if isinstance(_author_list, tuple):
                    author_list.append(_author_list)
                else:
                    author_list.extend(_author_list)
            else:
                author_list.append(tuple(re.split(r'\s{1,}', author)))
        return author_list

    def process_row(self, row, index):
        author_string = self.get_row_value('Author')
        journal_string = self.get_row_value('Journal')
        year = self.get_row_value('Year')
        try:
            date = datetime.strptime(year, '%Y')
        except ValueError:
            year = year[:-1]
            date = datetime.strptime(year, '%Y')
        title = self.get_row_value('Title')
        author_list = self.parse_author([author_string])
        authors = []

        for author_data in author_list:
            if len(author_data) == 1:
                first_name = last_name = author_data[0]
            else:
                first_name = author_data[len(author_data) - 1]
                last_name = ' '.join(author_data[:len(author_data) - 1])
            author, author_created = Author.objects.get_or_create(
                first_name=first_name,
                last_name=last_name
            )
            authors.append(author)

        journal, journal_created = Journal.objects.get_or_create(
            name=journal_string
        )

        entry, entry_created = Entry.objects.get_or_create(
            type='article',
            title=title,
            journal=journal,
            publication_date=date
        )

        rank = 0
        for author in authors:
            AuthorEntryRank.objects.get_or_create(
                entry=entry,
                author=author,
                rank=0
            )
            rank += 1

        source_reference, created = (
            SourceReferenceBibliography.objects.get_or_create(
                source=entry
            )
        )

        self.save_uuid(
            uuid=self.get_row_value('BioReferenceID'),
            object_id=source_reference.id
        )
