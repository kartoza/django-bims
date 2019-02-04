from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import F
from django.shortcuts import get_object_or_404
from bims.models import LocationSite, Biotope
from sass.models import SamplingMethod


class FishFormView(TemplateView):
    """View for fish form"""
    template_name = 'fish_form_page.html'
    location_site = None

    def get_context_data(self, **kwargs):
        context = super(FishFormView, self).get_context_data(**kwargs)
        if not self.location_site:
            return context
        context['location_site_name']  = self.location_site.name
        context['location_site_code']  = self.location_site.site_code
        context['location_site_lat'] = self.location_site.get_centroid().y
        context['location_site_long'] = self.location_site.get_centroid().x
        context['taxa'] = list(
            self.location_site.biological_collection_record.values(
                taxon_id=F('taxonomy'),
                taxon_name=F(
                    'taxonomy__'
                    'canonical_name'),
                rank=F('taxonomy__rank')
            ).distinct('taxonomy')
        )
        context['biotope_list'] = list(
            Biotope.objects.all().values(
                'name', 'description', 'display_order'
            ).order_by('display_order')
        )
        context['sampling_method_list'] = list(
            SamplingMethod.objects.all().values(
                'id', 'sampling_method'
            ).order_by(F('normalisation_factor').asc(nulls_first=True))
        )
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        site_id = request.GET.get('siteId', None)
        if site_id:
            self.location_site =  get_object_or_404(
                LocationSite,
                pk=site_id
            )

        return super(FishFormView, self).get(request, *args, **kwargs)
