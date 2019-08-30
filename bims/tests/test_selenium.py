import socket
from django.conf import settings
from django.db import IntegrityError
from django.contrib.auth import (
    SESSION_KEY, BACKEND_SESSION_KEY,
    get_user_model
)
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test import override_settings
from django.core.urlresolvers import reverse

from selenium import webdriver


@override_settings(ALLOWED_HOSTS=['*'])
class SeleniumTest(LiveServerTestCase):
    port = 8080

    @classmethod
    def setUpClass(cls):
        try:
            cls.host = socket.gethostbyname(socket.gethostname())
            """ Instantiate selenium driver instance """
            cls.selenium = webdriver.Remote(
                command_executor=settings.SELENIUM_DRIVER,
                desired_capabilities=webdriver.DesiredCapabilities.FIREFOX)
            cls.url = settings.SITEURL
            cls.selenium.implicitly_wait(5)
        except BaseException:
            raise Exception('Drivernya : ' + settings.SELENIUM_DRIVER)
        super(SeleniumTest, cls).setUpClass()


    @classmethod
    def tearDownClass(cls):
        """ Quit selenium driver instance """
        cls.selenium.quit()
        super(SeleniumTest, cls).tearDownClass()

    def create_session_cookie(self, username, password):
        # First, create a new test user
        user = get_user_model()
        user.objects.create_user(username=username, password=password)

        # Then create the authenticated session using the new user credentials
        session = SessionStore()
        session[SESSION_KEY] = user.pk
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session.save()

        # Finally, create the cookie dictionary
        cookie = {
            'name': settings.SESSION_COOKIE_NAME,
            'value': session.session_key,
            'secure': False,
            'path': '/',
        }
        return cookie

    def test_landing_page(self):
        # Display landing page
        url = reverse('landing-page')
        self.selenium.get(self.live_server_url + url)

        section_heading = self.selenium.find_element_by_class_name(
            'section-heading'
        )

        self.assertEqual(section_heading.text, u'BIODIVERSITY RECORDS')

    def test_sass_page_get_404(self):
        url = reverse('sass-form-page', kwargs={'site_id': 99})
        self.selenium.get(self.live_server_url + url)
        try:
            session_cookie = self.create_session_cookie(
                username='test@email.com',
                password='admin'
            )
            self.selenium.add_cookie(session_cookie)
        except IntegrityError:
            pass
        self.selenium.refresh()

        info = self.selenium.find_element_by_id('error-title')
        self.assertEqual(info.text,
                         '500 - SERVER ERROR')
