from django.db import models


class CITESListingInfo(models.Model):
    APPENDIX_CHOICES = [
        ('I', 'Appendix I'),
        ('II', 'Appendix II'),
        ('III', 'Appendix III'),
    ]

    appendix = models.CharField(
        max_length=3,
        choices=APPENDIX_CHOICES)
    annotation = models.TextField()
    effective_at = models.DateField()
    taxonomy = models.ForeignKey(
        'bims.Taxonomy',
        on_delete=models.CASCADE,
        related_name='cites_listing_infos')

    def __str__(self):
        return f"{self.appendix} - {self.taxonomy.name} - {self.effective_at}"
