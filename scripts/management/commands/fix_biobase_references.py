import re
from datetime import datetime, date
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from scripts.management.csv_command import CsvCommand
from bims.models import SourceReference, BiologicalCollectionRecord, ChemicalRecord
from bims.utils.user import create_users_from_string
from geonode.documents.models import Document


TAXON_GROUP = 'Taxon Group'
TAXON = 'Taxon'


class Command(CsvCommand):

    def csv_file_name(self, options):
        # Return name of the csv file
        return 'Biobase.Study.Reference.Table.For.DOI.URL.-.06-03-20.csv'

    def csv_dict_reader(self, csv_reader):
        for row in csv_reader:
            title = row['Title']
            fixed_title = re.sub(' +', ' ', title)
            url = row['URL']
            dul = row['Document Upload Link']
            reference_category = row['Reference category']
            source_references = SourceReference.objects.filter(
                Q(sourcereferencebibliography__source__title__icontains=title) |
                Q(sourcereferencedocument__source__title__icontains=title)
            )
            if source_references.exists():
                source_reference = source_references[0]
                if reference_category.lower() not in source_reference.reference_type.lower():
                    print('---Change to document---')
                    if dul:
                        try:
                            doc_split = dul.split('/')
                            document_id = int(doc_split[len(doc_split) - 1])
                            document = Document.objects.get(id=document_id)
                            print('---Create new source reference')
                            new_source_reference = (
                                SourceReference.create_source_reference(
                                    category='document',
                                    source_id=document.id,
                                    note=None
                                )
                            )
                            print('---Update bio records---')
                            BiologicalCollectionRecord.objects.filter(
                                source_reference=source_reference
                            ).update(
                                source_reference=new_source_reference
                            )
                            ChemicalRecord.objects.filter(
                                source_reference=source_reference
                            ).update(
                                source_reference=new_source_reference
                            )
                            print('---Delete old source reference---')
                            source_reference.delete()
                        except (ValueError, Document.DoesNotExist):
                            print ('Document {} does not exist'.format(
                                dul))
                    if url:
                        document_fields = {
                            'doc_url': url,
                            'title': fixed_title
                        }
                        if row['Year']:
                            document_fields['date'] = date(
                                year=int(row['Year']),
                                month=1,
                                day=1
                            )
                        authors = create_users_from_string(
                           row['Author(s)'])
                        if len(authors) > 0:
                            author = authors[0]
                        else:
                            author = None
                        document_fields['owner'] = author
                        document, document_created = Document.objects.get_or_create(
                            **document_fields
                        )
                        new_source_reference = (
                            SourceReference.create_source_reference(
                                category='document',
                                source_id=document.id,
                                note=None
                            )
                        )
                        print('---Update bio records---')
                        BiologicalCollectionRecord.objects.filter(
                            source_reference=source_reference
                        ).update(
                            source_reference=new_source_reference
                        )
                        ChemicalRecord.objects.filter(
                            source_reference=source_reference
                        ).update(
                            source_reference=new_source_reference
                        )
                        print('---Delete old source reference---')
                        source_reference.delete()
                    if reference_category.lower() == 'unpublished data':
                        print(fixed_title)
                else:
                    if title != fixed_title:
                        print('---Fix title---')
                        print(fixed_title)
                        source_reference.source.title = fixed_title
                        source_reference.source.save()
