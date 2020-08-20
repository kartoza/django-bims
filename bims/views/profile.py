from django.views.generic import DetailView
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, Http404
from bims.models.survey import Survey
from bims.models.location_site import LocationSite
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.source_reference import SourceReference


class ProfileView(DetailView):
    template_name = 'user/profile.html'
    model = get_user_model()
    slug_field = 'username'

    def post(self, request, *args, **kwargs):
        if 'slug' not in kwargs:
            raise Http404('Missing username')

        profile = self.model.objects.get(
            username=kwargs['slug']
        )
        if profile != self.request.user:
            raise Http404('Mismatch user')

        profile.first_name = self.request.POST.get('first-name', '')
        profile.last_name = self.request.POST.get('last-name', '')
        profile.bims_profile.role = self.request.POST.get('role', '')
        profile.organization = self.request.POST.get('organization', '')
        profile.bims_profile.save()
        profile.save()

        return HttpResponseRedirect(request.path_info)

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)

        # -- Collection records
        collection_records = BiologicalCollectionRecord.objects.filter(
            Q(survey__owner=self.object) |
            Q(survey__collector_user=self.object)
        ).distinct('id')
        context['total_records'] = collection_records.count()

        # -- Site visits
        site_visits = Survey.objects.filter(
            id__in=collection_records.values('survey')
        ).order_by('-date')

        context['site_visits'] = site_visits[0:10]

        # -- Total site visits
        context['total_site_visits'] = site_visits.count()

        # -- Contributions
        contributions = (
            site_visits.order_by('date').values('date').annotate(
                total=Count('biological_collection_record__id'))
        )
        context['contributions_date'] = [
            dt.strftime('%Y-%m-%d') for dt in contributions.values_list(
                'date', flat=True)]
        context['contributions_value'] = list(
            contributions.values_list('total', flat=True)
        )

        # -- Sites
        sites = LocationSite.objects.filter(
            owner=self.object
        )
        context['total_sites'] = sites.count()

        # -- Source references
        source_reference = (
            SourceReference.objects.filter(
                Q(sourcereferencebibliography__source__authors__user=
                  self.object) |
                Q(sourcereferencebibliography__document__bimsdocument__authors=
                  self.object) |
                Q(sourcereferencedocument__source__bimsdocument__authors=
                  self.object) |
                Q(sourcereferencedocument__source__owner=self.object))
        )
        context['source_references'] = source_reference[0:10]
        context['source_references_total'] = source_reference.count()

        return context
