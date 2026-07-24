import json
import logging
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
from bims.views.upload import _get_installation_token_and_repo

logger = logging.getLogger(__name__)


class BugReportView(LoginRequiredMixin, View):
    github_repo = ''

    def post(self, request, *args, **kwargs):
        self.github_repo = preferences.SiteSetting.github_feedback_repo

        if not self.github_repo:
            logger.error('BugReportView: github_feedback_repo is not configured')
            return JsonResponse({'status': 'ERROR', 'message': 'Missing GitHub repo configuration'}, status=500)

        try:
            report = self.create_report(**request.POST.dict())
        except TypeError as e:
            logger.error('BugReportView: incorrect POST body: %s', e)
            return JsonResponse({'status': 'ERROR', 'message': 'Incorrect POST body'}, status=400)
        except BadCredentialsException as e:
            logger.error('BugReportView: invalid GitHub credentials: %s', e)
            return JsonResponse({'status': 'ERROR', 'message': 'Invalid GitHub credentials'}, status=500)
        except UnknownObjectException as e:
            logger.error('BugReportView: GitHub repository not found: %s', e)
            return JsonResponse({'status': 'ERROR', 'message': 'GitHub repository not found'}, status=500)
        except Http404 as e:
            logger.error('BugReportView: GitHub App config error: %s', e)
            return JsonResponse({'status': 'ERROR', 'message': str(e)}, status=500)
        except GithubException as ge:
            msg = ge.data.get('message') if getattr(ge, 'data', None) else str(ge)
            logger.error('BugReportView: GitHub error: %s', msg)
            return JsonResponse({'status': 'ERROR', 'message': f'GitHub error: {msg}'}, status=500)
        except Exception as e:
            logger.exception('BugReportView: unexpected error: %s', e)
            return JsonResponse({'status': 'ERROR', 'message': 'Unexpected error'}, status=500)

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
        token, repo_full = _get_installation_token_and_repo(self.github_repo)
        g = Github(auth=Auth.Token(token))
        repo = g.get_repo(repo_full, lazy=False)

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
