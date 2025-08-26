from django.db import models
from ordered_model.models import OrderedModel


class CustomFont(OrderedModel):
    """Fonts available in CKEditor & frontend."""
    name = models.CharField(
        max_length=100,
        help_text="Font family name as used in CSS (e.g., Inter, 'Noto Serif Display')."
    )
    css_url = models.URLField(
        max_length=512,
        help_text="Stylesheet URL (e.g., https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap)"
    )
    stack = models.CharField(
        max_length=512,
        blank=True,
        help_text="CSS font-family stack. Leave blank to use the 'name' only."
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def font_stack(self):
        return self.stack.strip() or self.name.strip()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Custom fonts'
        ordering = ['order']
