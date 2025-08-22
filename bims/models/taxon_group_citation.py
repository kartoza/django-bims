# bims/models/taxon_group_citation.py
from django.db import models
from django.utils import timezone


def current_year():
    return timezone.now().year


class TaxonGroupCitation(models.Model):
    """
    Admin-managed citation metadata per organism (taxon) group.
    Year and access_date are filled automatically.
    """
    taxon_group = models.ForeignKey(
        'bims.TaxonGroup',
        on_delete=models.CASCADE,
        related_name="citations",
        help_text="Organism group this citation refers to."
    )
    authors = models.CharField(
        max_length=500,
        help_text='Author(s), e.g. "Doe J., Smith A."'
    )
    citation_text = models.CharField(
        max_length=500,
        help_text='Citation title/text, e.g. "Ostracoda Checklist; Freshwater Animal Diversity Assessment (FADA)".'
    )
    year = models.PositiveSmallIntegerField(
        default=current_year,
        help_text="Publication year (defaults to current year)."
    )
    access_date = models.DateField(
        default=timezone.now,
        help_text="Access date (defaults to today)."
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = "Taxon Group Citation"
        verbose_name_plural = "Taxon Group Citations"
        ordering = ("taxon_group__display_order", "taxon_group__name")

    def __str__(self):
        return f"{self.taxon_group.name} — {self.year}"

    @property
    def formatted_citation(self) -> str:
        """
        Example:
        Doe J., Smith A. (2025). Ostracoda Checklist; Freshwater Animal Diversity Assessment (FADA). Accessed 2025-08-22.
        """
        ad = self.access_date.isoformat() if self.access_date else ""
        return f"{self.authors} ({self.year}). {self.citation_text}. Accessed {ad}."

    def clean(self):
        from django.core.exceptions import ValidationError
        y = int(self.year or 0)
        if y < 1500 or y > timezone.now().year + 1:
            raise ValidationError({"year": "Please enter a reasonable publication year."})
