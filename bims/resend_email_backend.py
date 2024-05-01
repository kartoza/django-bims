import base64
import mimetypes

import requests
from preferences import preferences
from django.core.mail.backends.base import BaseEmailBackend


class ResendBackend(BaseEmailBackend):
    """
    A Django email backend that uses the Resend API.
    """
    def send_messages(self, email_messages):
        """
        Send a list of email messages using the Resend API.
        :param email_messages: List of Django email messages.
        :return: The number of successfully sent messages.
        """
        count = 0

        for email in email_messages:
            response = self._send_via_resend(email)

            if response.status_code == 200:
                count += 1

        return count

    def _send_via_resend(self, email):
        """
        Send a single email via Resend.
        :param email: A Django EmailMessage object.
        :return: The response from the Resend API.
        """
        resend_api_key = preferences.SiteSetting.resend_api_key
        from_email = (
            preferences.SiteSetting.default_from_email if
            preferences.SiteSetting.default_from_email else
            email.from_email
        )

        # Prepare the payload for the Resend API request
        payload = {
            "from": from_email,
            "to": email.to,
            "subject": email.subject,
            "text": email.body,
        }

        if email.content_subtype == "html":
            payload["html"] = email.body

        # Check for HTML content
        if email.alternatives:
            for alternative in email.alternatives:
                content_type, content = alternative
                if content_type == "text/html":
                    payload["html"] = content

        attachments = []

        for attachment in email.attachments:
            if isinstance(attachment, tuple):
                filename, content, mime_type = attachment
                encoded_content = base64.b64encode(content).decode("utf-8")
            else:
                filename = attachment
                with open(attachment, "rb") as f:
                    content = f.read()
                mime_type, _ = mimetypes.guess_type(filename)
                encoded_content = base64.b64encode(content).decode("utf-8")

            attachments.append({
                "filename": filename,
                "content": encoded_content,
                "content_type": mime_type,
            })

        if attachments:
            payload["attachments"] = attachments

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json",
        }

        # Make the request to the Resend API
        resend_url = "https://api.resend.com/emails"
        response = requests.post(resend_url, json=payload, headers=headers)
        return response
