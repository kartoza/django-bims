import json
from django.views import View
from django.http import JsonResponse
from django.http import Http404
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from braces.views import LoginRequiredMixin
from github import Github
from preferences import preferences


class BugReportView(LoginRequiredMixin, View):
    github_access_token = ''
    github_repo = ''

    def post(self, request, *args, **kwargs):
        self.github_access_token = (
            preferences.SiteSetting.github_feedback_token
        )
        self.github_repo = (
            preferences.SiteSetting.github_feedback_repo
        )
        if not self.github_access_token or not self.github_repo:
            raise Http404('Missing access token or github repo name')
        try:
            report = self.create_report(**request.POST.dict())
        except TypeError:
            raise Http404('Incorrect POST body')
        self.send_email(report.number, report.title)
        return JsonResponse({
            'status': 'OK',
            'ticket_number': report.number
        })

    def create_report(self, summary, description, labels,
                      json_additional_information=None):
        """
        Create a report in github repo
        :return: report object
        """
        g = Github(self.github_access_token)
        repo = g.get_repo(self.github_repo)
        report_template = 'notifications/ticket_body.txt'
        additional_information = ''
        if json_additional_information:
            all_information = json.loads(json_additional_information)
            for information_key in all_information:
                value = all_information[information_key]
                if value[:4] != 'http':
                    value = value.capitalize()
                additional_information += '{key}: {value}\n'.format(
                    key=information_key.capitalize(),
                    value=value
                )

        ticket_body = render_to_string(
            report_template,
            {
                'user_id': self.request.user.id,
                'description': description.capitalize(),
                'current_site': Site.objects.get_current(),
                'additional_information': additional_information
            }
        )

        report = repo.create_issue(
            title=summary.capitalize(),
            body=ticket_body,
            labels=labels.split(','))
        return report

    def send_email(self, ticket_number, summary):
        """
        Send email to reporter and also admin users to notify there is new
        report
        """
        # Send to admins
        email_template = 'notifications/ticket_created'
        admins = get_user_model().objects.filter(is_superuser=True)
        ctx = {
            'username': self.request.user.email,
            'current_site': Site.objects.get_current(),
            'github_repo': self.github_repo,
            'ticket_number': ticket_number,
            'summary': summary
        }
        subject = render_to_string(
            '{0}_subject.txt'.format(email_template),
            ctx
        )
        message = render_to_string(
            '{}_message_admins.txt'.format(email_template),
            ctx
        )
        msg = EmailMultiAlternatives(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            list(admins.values_list('email', flat=True)))
        msg.send()

        # Send to reporter
        user_message = render_to_string(
            '{}_message_user.txt'.format(email_template),
            ctx
        )
        msg = EmailMultiAlternatives(
            subject,
            user_message,
            settings.DEFAULT_FROM_EMAIL,
            [self.request.user.email])
        msg.send()
