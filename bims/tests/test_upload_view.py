# coding=utf-8
import io
from datetime import timedelta
from unittest import mock
from unittest.mock import patch, MagicMock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from requests import RequestException
from rest_framework import status

from preferences import preferences
from github.GithubException import UnknownObjectException

from bims.models.upload_request import UploadRequest, UploadType


UPLOAD_URL_NAME = "upload"


class TestUploadView(FastTenantTestCase):
    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        try:
            self.url = reverse(UPLOAD_URL_NAME)
        except Exception:
            self.url = "/upload/"

    def _make_file(self, name="data.csv", content=b"col1,col2\nx,y\n"):
        return SimpleUploadedFile(name, content, content_type="text/csv")

    def _mock_github_success(self):
        """
        Patch GithubIntegration and Github to simulate successful issue creation.
        Returns the context managers so you can use 'with' to scope them.
        """
        fake_integ = MagicMock()
        fake_install = MagicMock()
        fake_install.id = 42
        fake_integ.get_repo_installation.return_value = fake_install

        fake_access = MagicMock()
        fake_access.token = "tok_abc"
        fake_access.expires_at = timezone.now() + timedelta(minutes=60)
        fake_integ.get_access_token.return_value = fake_access

        fake_issue = MagicMock()
        fake_issue.number = 321
        fake_issue.html_url = "https://github.com/owner/repo/issues/321"

        fake_repo = MagicMock()
        fake_repo.create_issue.return_value = fake_issue

        fake_gh = MagicMock()
        fake_gh.return_value.get_repo.return_value = fake_repo

        p_integ = patch("bims.views.upload.GithubIntegration", return_value=fake_integ)
        p_gh = patch("bims.views.upload.Github", fake_gh)
        return p_integ, p_gh, fake_repo

    def _post_payload(self, **overrides):
        data = {
            "title": "test",
            "name": "Jane Doe",
            "email": "jane@example.org",
            "upload_type": "occurrence",
            "notes": "hello",
            "source": "upload_portal",
            "upload_file": self._make_file(),
        }
        data.update(overrides)
        return data

    def test_get_page_ok(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(b"Upload", res.content)


    @mock.patch("bims.views.upload.preferences")
    def test_post_success_without_recaptcha(self, mock_preferences):
        mock_preferences.SiteSetting.recaptcha_site_key = ""
        mock_preferences.SiteSetting.recaptcha_secret_key = ""
        mock_preferences.SiteSetting.github_feedback_repo = "owner/repo"

        mock_preferences.SiteSetting.default_site_name = "FBIS Africa"
        mock_preferences.SiteSetting.github_app_id = "12345"
        mock_preferences.SiteSetting.github_private_key = "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----"
        mock_preferences.SiteSetting.github_upload_assignees = "alice,bob"

        p_integ, p_gh, fake_repo = self._mock_github_success()
        with p_integ, p_gh:
            res = self.client.post(self.url, data=self._post_payload())
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        payload = res.json()
        self.assertEqual(payload["status"], "OK")
        self.assertIn("ticket_number", payload)
        # upload request created
        self.assertEqual(UploadRequest.objects.count(), 1)
        ur = UploadRequest.objects.first()
        self.assertEqual(ur.name, "Jane Doe")
        self.assertEqual(ur.email, "jane@example.org")
        # assignees passed correctly
        kwargs = fake_repo.create_issue.call_args.kwargs
        self.assertEqual(kwargs.get("assignees"), ["alice", "bob"])
        self.assertIn("upload", kwargs.get("labels", []))


    @mock.patch("bims.views.upload.preferences")
    def test_post_with_recaptcha_missing_token_returns_400(self, mock_preferences):
        mock_preferences.SiteSetting.github_feedback_repo = "owner/repo"
        mock_preferences.SiteSetting.recaptcha_site_key = "sitekey123"
        mock_preferences.SiteSetting.recaptcha_secret_key = "secret456"

        p_integ, p_gh, _ = self._mock_github_success()
        with p_integ, p_gh:
            res = self.client.post(self.url, data=self._post_payload())
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("recaptcha", res.json().get("errors", {}))

    @mock.patch("bims.views.upload.preferences")
    def test_post_with_recaptcha_success(self, mock_preferences):
        mock_preferences.SiteSetting.github_feedback_repo = "owner/repo"
        mock_preferences.SiteSetting.recaptcha_site_key = "sitekey123"
        mock_preferences.SiteSetting.recaptcha_secret_key = "secret456"
        mock_preferences.SiteSetting.default_site_name = "FBIS Africa"
        mock_preferences.SiteSetting.github_app_id = "12345"
        mock_preferences.SiteSetting.github_private_key = "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----"
        mock_preferences.SiteSetting.github_upload_assignees = "alice,bob"

        # Mock Google verification success
        def _mock_json_ok():
            return {"success": True, "score": 0.9, "action": "upload"}

        mock_resp = MagicMock()
        mock_resp.json.side_effect = _mock_json_ok

        p_requests = patch("bims.views.upload.requests.post", return_value=mock_resp)

        p_integ, p_gh, _ = self._mock_github_success()
        with p_requests, p_integ, p_gh:
            res = self.client.post(
                self.url,
                data=self._post_payload(recaptcha_token="tok_recaptcha_ok"),
            )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["status"], "OK")
        self.assertEqual(UploadRequest.objects.count(), 1)

    @mock.patch("bims.views.upload.preferences")
    def test_post_with_recaptcha_network_error(self, mock_preferences):
        mock_preferences.SiteSetting.github_feedback_repo = "owner/repo"
        mock_preferences.SiteSetting.recaptcha_site_key = "sitekey123"
        mock_preferences.SiteSetting.recaptcha_secret_key = "secret456"
        mock_preferences.SiteSetting.default_site_name = "FBIS Africa"
        mock_preferences.SiteSetting.github_app_id = "12345"
        mock_preferences.SiteSetting.github_private_key = "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----"
        mock_preferences.SiteSetting.github_upload_assignees = "alice,bob"

        p_requests = patch("bims.views.upload.requests.post", side_effect=RequestException)

        p_integ, p_gh, _ = self._mock_github_success()
        with p_requests, p_integ, p_gh:
            res = self.client.post(
                self.url,
                data=self._post_payload(recaptcha_token="tok_recaptcha"),
            )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.json()["status"], "ERROR")

    def test_github_unknown_object_yields_404(self):
        # reCAPTCHA disabled
        preferences.SiteSetting.recaptcha_site_key = ""
        preferences.SiteSetting.recaptcha_secret_key = ""

        # Mock GitHub so that create_issue raises UnknownObjectException
        fake_integ = MagicMock()
        fake_install = MagicMock()
        fake_install.id = 42
        fake_integ.get_repo_installation.return_value = fake_install

        fake_access = MagicMock()
        fake_access.token = "tok_abc"
        fake_access.expires_at = timezone.now() + timedelta(minutes=60)
        fake_integ.get_access_token.return_value = fake_access

        fake_repo = MagicMock()
        fake_repo.create_issue.side_effect = UnknownObjectException(
            status=404, data={"message": "Not found"}, headers={}
        )
        fake_gh = MagicMock()
        fake_gh.return_value.get_repo.return_value = fake_repo

        with patch("bims.views.upload.GithubIntegration", return_value=fake_integ), \
             patch("bims.views.upload.Github", fake_gh):
            res = self.client.post(self.url, data=self._post_payload())

        # The view maps UnknownObjectException to Http404
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
