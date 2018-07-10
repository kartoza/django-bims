# coding=utf-8
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from bims.models.biological_collection_record import BiologicalCollectionRecord


class ContributionsView(TemplateView):
    template_name = 'contributions.html'

    def get_context_data(self, **kwargs):
        """Get the context data which is passed to a template.

        :param kwargs: Any arguments to pass to the superclass.
        :type kwargs: dict

        :returns: Context data which will be passed to the template.
        :rtype: dict
        """
        context = super(ContributionsView, self).get_context_data(**kwargs)
        all_records = BiologicalCollectionRecord.objects.all()
        contributors = User.objects.filter(
            id__in=all_records.values('owner__id')
        ).order_by('first_name', 'last_name', 'username')

        context['contributors'] = contributors
        return context
