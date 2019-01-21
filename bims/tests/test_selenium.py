import socket
from django.conf import settings
from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test import override_settings
from django.core.urlresolvers import reverse
from bims.tests.model_factories import LocationSiteF
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

        info = self.selenium.find_element_by_id('description')
        self.assertEqual(info.text,
                         'Page Not Found')
