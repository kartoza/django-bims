# coding: utf-8
__author__ = 'Alison Mukoma <alison@kartoza.com>'
__copyright__ = 'kartoza.com'

from django.views.generic import TemplateView
# from braces.views import LoginRequiredMixin


class LinksPageView(TemplateView):
	"""View to show the links page."""
	template_name = 'links.html'

	def get_context_data(self, **kwargs):
		context = super(LinksPageView, self).get_context_data(**kwargs)
		context['Titile'] = 'Links Page'
		return context
