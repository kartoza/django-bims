from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.urls import reverse
from bims.models.confidence_score import DataConfidenceScore
from bims.utils.domain import get_current_domain


class AbstractValidation(DataConfidenceScore):
    """Simple Abstract Validation model
    """
    EMAIL_REJECTION_SUBJECT = 'Your data has been rejected'
    EMAIL_APPROVED_SUBJECT = 'Your data has been approved'
    EMAIL_REJECTION_TEMPLATE = 'email/data_rejection'
    EMAIL_APPROVED_TEMPLATE = 'email/data_validated'
    EMAIL_DATA_SITE_NAME = 'site_name'
    EMAIL_DATA_COLLECTION_NAME = 'data_name'
    EMAIL_DATA_REASONS = 'reason'
    EMAIL_DATA_URL = 'data_url'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        blank=True,
        null=True,
    )
    collector_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text='The user object of the actual capturer/collector '
                  'of this data',
        null=True,
        blank=True,
        related_name='%(class)s_collector_user',
        on_delete=models.SET_NULL
    )
    analyst = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text='The person that did the analysis',
        null=True,
        blank=True,
        related_name='%(class)s_analyst',
        on_delete=models.SET_NULL
    )

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

    end_embargo_date = models.DateField(
        null=True,
        blank=True,
        help_text=(
            'The date when the embargo on the data expires. '
            'After this date, the data will become public.'
        ),
    )

    source_site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Associated Site",
        help_text="The site this record is associated with."
    )

    class Meta:
        abstract = True

    def _is_rejected(self):
        return not self.validated and self.rejected

    is_rejected = property(_is_rejected)

    def _is_validated(self):
        return self.validated and not self.rejected

    is_validated = property(_is_validated)

    @property
    def data_name(self):
        raise NotImplementedError

    @property
    def validation_status(self):
        if self.ready_for_validation:
            return '<span class="badge badge-warning">In Review</span>'
        else:
            if self.validated:
                return (
                    '<span class="badge badge-success">Validated</span>'
                )
            else:
                return (
                    '<span class="badge badge-secondary">Unvalidated</span>'
                )

    def validate(self, show_redirect_url=True):
        self.validated = True
        self.rejected = False
        self.ready_for_validation = False
        self.save()

        self.send_notification_email(
            subject=self.EMAIL_APPROVED_SUBJECT,
            email_template=self.EMAIL_APPROVED_TEMPLATE,
            show_redirect_url=show_redirect_url
        )

    def reject(self, rejection_message, show_redirect_url=True, **kwargs):
        self.validated = False
        self.rejected = True
        self.ready_for_validation = False
        if self.owner is None:
            self.save()
            return
        elif rejection_message:
            self.validation_message = rejection_message
        self.save()

        self.send_notification_email(
            subject=self.EMAIL_REJECTION_SUBJECT,
            email_template=self.EMAIL_REJECTION_TEMPLATE,
            show_redirect_url=show_redirect_url
        )

    def ready_to_be_validate(self):
        self.validated = False
        self.rejected = False
        self.ready_for_validation = True
        self.save()

    def send_notification_email(self,
                                subject='',
                                email_template='',
                                show_redirect_url=True):
        site_domain_name = get_current_domain()
        subject_email = '[%s]%s' % (
            site_domain_name,
            subject)

        if show_redirect_url:
            data_update_url = '%s%s' % (
                site_domain_name,
                reverse('site-visit-detail', args=(self.pk, ))
            )
        else:
            data_update_url = ''

        msg_data = {
            self.EMAIL_DATA_SITE_NAME: site_domain_name,
            self.EMAIL_DATA_REASONS: self.validation_message,
            self.EMAIL_DATA_URL: data_update_url,
            self.EMAIL_DATA_COLLECTION_NAME: self.data_name
        }

        msg_plain = render_to_string(
            email_template + '.txt',
            msg_data
        )

        if self.owner:
            send_mail(
                subject=subject_email,
                message=msg_plain,
                from_email=settings.SERVER_EMAIL,
                recipient_list=[self.owner.email]
            )
