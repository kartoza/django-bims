from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel
from django.db.models import Q


class ManualPage(Page):
    intro = RichTextField(blank=True)
    body = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        FieldPanel('body'),
    ]

    def get_children_with_permission(self, page, request):
        pages = page.get_children()
        if not request.user.is_authenticated:
            # only pages with no view restrictions at all
            pages = pages.public()
        else:
            if request.user.is_superuser:
                return pages
            pages = pages.filter(
                # pages with no view restrictions
                Q(view_restrictions__isnull=True) |
                # pages restricted to any logged-in user
                Q(view_restrictions__restriction_type='login') |
                # pages restricted by group
                Q(view_restrictions__restriction_type='groups',
                    view_restrictions__groups__in=request.user.groups.all())
            )
        return pages

    def get_children_menu(self, page, request):
        menu = []
        for child in self.get_children_with_permission(page, request):
            children_data = {
                'title': child.title,
                'slug': child.slug,
                'url': child.url
            }
            if child.get_children():
                children_data['children'] = self.get_children_menu(
                    child, request
                )
            menu.append(children_data)
        return menu

    def get_context(self, request, *args, **kwargs):
        context = super(ManualPage, self).get_context(request, *args, **kwargs)
        ancestors = self.get_ancestors()
        if len(ancestors) > 1:
            page = ancestors[1]
        else:
            page = self
        menu = self.get_children_menu(page, request)
        context['menu'] = menu

        return context
