import json
from typing import List

from django.views import View
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
from braces.views import LoginRequiredMixin

from github import Github, Auth
from github.GithubException import GithubException, BadCredentialsException, UnknownObjectException

from preferences import preferences
from bims.utils.domain import get_current_domain


class BugReportView(LoginRequiredMixin, View):
    github_access_token = ''
    github_repo = ''

    def post(self, request, *args, **kwargs):
        self.github_access_token = preferences.SiteSetting.github_feedback_token
        self.github_repo = preferences.SiteSetting.github_feedback_repo

        if not self.github_access_token or not self.github_repo:
            raise Http404('Missing access token or GitHub repo name')

        try:
            report = self.create_report(**request.POST.dict())
        except TypeError:
            raise Http404('Incorrect POST body')
        except BadCredentialsException:
            raise Http404('Invalid GitHub credentials')
        except UnknownObjectException:
            raise Http404('GitHub repository not found')
        except GithubException as ge:
            raise Http404(f'GitHub error: {ge.data.get("message") if getattr(ge, "data", None) else str(ge)}')

        self.send_email(report.number, report.title)

        return JsonResponse({
            'status': 'OK',
            'ticket_number': report.number
        })

    def _normalize_labels(self, labels: str) -> List[str]:
        """
        Split a comma-separated labels string into a clean list.
        Keeps behavior of passing raw strings to GitHub (labels must exist on the repo).
        """
        if not labels:
            return []
        return [l.strip() for l in labels.split(',') if l.strip()]

    def create_report(self, summary, description, labels,
                      json_additional_information=None):
        """
        Create a report (issue) in the configured GitHub repo.
        :return: Issue object
        """
        auth = Auth.Token(self.github_access_token)
        g = Github(auth=auth)
        repo = g.get_repo(self.github_repo, lazy=False)

        report_template = 'notifications/ticket_body.txt'

        additional_information = ''
        if json_additional_information:
            try:
                all_information = json.loads(json_additional_information)
                for information_key, value in all_information.items():
                    if isinstance(value, str) and not value.startswith('http'):
                        value = value.capitalize()
                    additional_information += f'{information_key.capitalize()}: {value}\n'
            except (ValueError, TypeError):
                pass

        ticket_body = render_to_string(
            report_template,
            {
                'user_id': self.request.user.id,
                'description': (description or '').capitalize(),
                'current_site': get_current_domain(),
                'additional_information': additional_information
            }
        )

        label_list = self._normalize_labels(labels)

        report = repo.create_issue(
            title=(summary or '').capitalize(),
            body=ticket_body,
            labels=label_list or None
        )
        return report

    def send_email(self, ticket_number, summary):
        """
        Send email to reporter and superusers to notify that a new report exists.
        """
        email_template = 'notifications/ticket_created'
        admins = get_user_model().objects.filter(is_superuser=True)

        ctx = {
            'username': self.request.user.email,
            'current_site': get_current_domain(),
            'github_repo': self.github_repo,
            'ticket_number': ticket_number,
            'summary': summary
        }

        subject = render_to_string(f'{email_template}_subject.txt', ctx).strip()

        message_admins = render_to_string(f'{email_template}_message_admins.txt', ctx)
        if admins.exists():
            msg_admins = EmailMultiAlternatives(
                subject,
                message_admins,
                settings.DEFAULT_FROM_EMAIL,
                list(admins.values_list('email', flat=True))
            )
            msg_admins.send()

        # Reporter
        user_message = render_to_string(f'{email_template}_message_user.txt', ctx)
        msg_user = EmailMultiAlternatives(
            subject,
            user_message,
            settings.DEFAULT_FROM_EMAIL,
            [self.request.user.email]
        )
        msg_user.send()
