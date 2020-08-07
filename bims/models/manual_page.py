from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from wagtail.admin.edit_handlers import PageChooserPanel
from django.db import models


class ManualPage(Page):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        FieldPanel('body', classname="full"),
    ]

    def get_children_menu(self, page):
        menu = []
        for child in page.get_children():
            data = {
                'title': child.title,
                'slug': child.slug,
                'url': child.url
            }
            if child.get_children():
                data['children'] = self.get_children_menu(child)
            menu.append(data)
        return menu

    def get_context(self, request, *args, **kwargs):
        context = super(ManualPage, self).get_context(request, *args, **kwargs)
        ancestors = self.get_ancestors()
        if len(ancestors) > 1:
            page = ancestors[1]
        else:
            page = self
        menu = self.get_children_menu(page)
        context['menu'] = menu

        return context