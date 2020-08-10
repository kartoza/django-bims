from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel


class ManualPage(Page):
    intro = RichTextField(blank=True)
    body = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        FieldPanel('body'),
    ]

    def get_children_menu(self, page):
        menu = []
        for child in page.get_children():
            children_data = {
                'title': child.title,
                'slug': child.slug,
                'url': child.url
            }
            if child.get_children():
                children_data['children'] = self.get_children_menu(child)
            menu.append(children_data)
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
