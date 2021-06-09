from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.urls import reverse


class AbstractValidation(models.Model):
    """Simple Abstract Validation model
    """
    EMAIL_REJECTION_SUBJECT = 'Your data has been rejected'
    EMAIL_REJECTION_TEMPLATE = 'email/data_rejection'
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

    def validate(self):
        self.validated = True
        self.rejected = False
        self.ready_for_validation = False
        self.save()

    def reject(self, rejection_message, **kwargs):
        self.validated = False
        self.rejected = True
        self.ready_for_validation = False
        if self.owner is None:
            self.save()
            return
        elif rejection_message:
            self.validation_message = rejection_message
        self.save()
        self._send_rejection_email(**kwargs)

    def ready_to_be_validate(self):
        self.validated = False
        self.rejected = False
        self.ready_for_validation = True
        self.save()

    def _send_rejection_email(self, **kwargs):
        site_domain_name = Site.objects.get_current().domain
        subject_email = '[%s]%s' % (
            site_domain_name,
            self.EMAIL_REJECTION_SUBJECT)
        data_update_url = '%s%s' % (
            site_domain_name,
            reverse('update-records', args=(self.pk, ))
        )

        msg_data = {
            self.EMAIL_DATA_SITE_NAME: site_domain_name,
            self.EMAIL_DATA_REASONS: self.validation_message,
            self.EMAIL_DATA_URL: data_update_url,
            self.EMAIL_DATA_COLLECTION_NAME: self.data_name
        }

        msg_plain = render_to_string(
            self.EMAIL_REJECTION_TEMPLATE + '.txt',
            msg_data
        )
        msg_html = render_to_string(
            self.EMAIL_REJECTION_TEMPLATE + '.html',
            msg_data
        )

        send_mail(
            subject=subject_email,
            message=msg_plain,
            from_email=settings.SERVER_EMAIL,
            recipient_list=[self.owner.email],
            html_message=msg_html
        )
