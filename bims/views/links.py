# coding: utf-8
__author__ = 'Alison Mukoma <alison@kartoza.com>'
__copyright__ = 'kartoza.com'

from django.views.generic import TemplateView
from simple_links.models import Category, Link


class LinksPageView(TemplateView):
	"""View to show the links page."""

	template_name = 'links.html'

	def get_context_data(self, **kwargs):

		context = super(LinksPageView, self).get_context_data(**kwargs)
		context['Titile'] = 'Links Page'
		categories = Category.objects.all()

		context['data_list'] = []
		for category in categories:
			category_links = {'category': category, 'links': []}

			links_qs = Link.objects.filter(category=category.pk)
			for link in links_qs:
				category_links['links'].append(link)
			context['data_list'].append(category_links)


			context['category_links'] = category_links
			context['categoriez'] = categories

		return context
