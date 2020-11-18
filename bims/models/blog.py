from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.api import APIField
from wagtail.admin.edit_handlers import (
    FieldPanel,
    PageChooserPanel
)
from wagtail.images.edit_handlers import ImageChooserPanel
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models


class BlogPage(Page):
    intro = RichTextField(blank=True)
    intro_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    body = RichTextField(blank=True)
    related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    # Export fields over the API
    api_fields = [
        APIField('intro'),
        APIField('body'),
        APIField('authors'),
        APIField('intro_image')
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        ImageChooserPanel('intro_image'),
        FieldPanel('body', classname="full"),
        PageChooserPanel('related_page', ['bims.BlogPage', 'bims.ManualPage']),
    ]

    # taken from
    # https://learnwagtail.com/tutorials/how-to-paginate-your-wagtail-pages/
    def get_context(self, request, *args, **kwargs):
        """Adding custom stuff to our context."""
        context = super(BlogPage, self).get_context(request, *args, **kwargs)
        # Get all posts
        all_posts = self.get_children().public().order_by(
            '-first_published_at')
        # Paginate all posts by 5 per page
        paginator = Paginator(all_posts, 5)
        # Try to get the ?page=x value
        page = request.GET.get("page")
        try:
            # If the page exists and the ?page=x is an int
            posts = paginator.page(page)
        except PageNotAnInteger:
            # If the ?page=x is not an int; show the first page
            posts = paginator.page(1)
        except EmptyPage:
            # If the ?page=x is out of range (too high most likely)
            # Then return the last page
            posts = paginator.page(paginator.num_pages)

        # "posts" will have child pages; you'll need to use .
        # specific in the template
        # in order to access child properties, s
        # uch as youtube_video_id and subtitle
        context["posts"] = posts
        return context
