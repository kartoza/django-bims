import socket
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.core.urlresolvers import reverse
from selenium import webdriver


@override_settings(ALLOWED_HOSTS=['*'])
class SeleniumTest(StaticLiveServerTestCase):
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

    def test_landing_page(self):
        # Display landing page
        url = reverse('landing-page')
        self.selenium.get(self.live_server_url + url)

        section_heading = self.selenium.find_element_by_class_name(
            'section-heading'
        )

        self.assertEqual(section_heading.text, u'BIODIVERSITY RECORDS')
