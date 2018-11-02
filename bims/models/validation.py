from django.db import models

class AbstractValidation(models.Model):
    """Simple Abstract Validation model
    """
    validated = models.BooleanField(
        default=False
    )

    rejected = models.BooleanField(
        default=False
    )

    ready_for_validation = models.BooleanField(
        default=False
    )

    validation_message = models.TextField(
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

    def _is_rejected(self):
        return not self.validated and self.rejected

    is_rejected = property(_is_rejected)

    def _is_validated(self):
        return self.validated and not self.rejected

    is_validated = property(_is_validated)

    def validate(self):
        self.validated = True
        self.rejected = False
        self.ready_for_validation = False
        self.save()

    def reject(self, rejection_message):
        self.validated = False
        self.rejected = True
        self.ready_for_validation = False
        if rejection_message:
            self.validation_message = rejection_message
        self.save()

    def ready_to_be_validate(self):
        self.validated = False
        self.rejected = False
        self.ready_for_validation = True
        self.save()
