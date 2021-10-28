from requests.exceptions import HTTPError
from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response

from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest, HttpResponseServerError
from django.core.validators import URLValidator

from td_biblio.exceptions import DOILoaderError
from td_biblio.models.bibliography import Entry
from td_biblio.utils.loaders import DOILoader
from td_biblio.utils.format_validator import BibliographyFormatValidator
from td_biblio.serializer.bibliography import EntrySerializer

from bims.models.source_reference import SourceReferenceBibliography


class GetBibliographyByDOI(LoginRequiredMixin, APIView):
    """ Get bibliography by doi.
    Also autosave into our bibliography model """

    def get(self, request):
        query = request.GET.get('q', None)
        if not query:
            return HttpResponseBadRequest('q parameter is needed')

        # Check if query is url
        try:
            URLValidator()(query)
            try:
                entry = Entry.objects.get(url__iexact=query)
            except Entry.DoesNotExist:
                return HttpResponseBadRequest('%s is not found' % query)
            except Entry.MultipleObjectsReturned:
                entry = Entry.objects.filter(url__iexact=query).first()
        except ValidationError:
            try:
                BibliographyFormatValidator.doi_format_validation(query)
            except ValidationError as e:
                return HttpResponseBadRequest(e)

            # Save this doi into our bibliography
            try:
                entry = Entry.objects.get(doi__iexact=query)
            except Entry.DoesNotExist:
                doi_loader = DOILoader()

                try:
                    doi_loader.load_records(DOIs=[query])
                except DOILoaderError as e:
                    return HttpResponseBadRequest(e)
                except HTTPError:
                    return HttpResponseBadRequest('%s is not found' % query)

                doi_loader.save_records()

                try:
                    entry = Entry.objects.get(doi__iexact=query)
                except Entry.DoesNotExist:
                    return HttpResponseServerError(
                        '%s can not be created. '
                        'Please ask administration' % query)

        serializer_data = EntrySerializer(entry).data

        source_reference = SourceReferenceBibliography.objects.filter(
            source=entry
        )

        serializer_data['data_exist'] = source_reference.exists()

        return Response(serializer_data)
