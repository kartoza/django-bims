from django.test import TestCase
from bims_theme.tests.model_factories import (
    CustomThemeF,
    PartnerF,
    CarouselHeaderF
)
from bims_theme.context_processor import bims_custom_theme


class TestCustomLandingPage(TestCase):

    def setUp(self):
        pass

    def test_add_carousel_to_custom_theme(self):
        carousel_1 = CarouselHeaderF.create(
            title='carousel_1',
            order=0
        )
        CustomThemeF.create(
            carousels=[carousel_1]
        )
        self.assertIn(
            carousel_1,
            bims_custom_theme(self)['custom_theme'].carousels.all()
        )

    def test_add_partner_to_custom_theme(self):
        partner = PartnerF.create(
            order=0
        )
        CustomThemeF.create(
            partners=[partner]
        )
        self.assertIn(
            partner,
            bims_custom_theme(self)['custom_theme'].partners.all()
        )

    def test_elements_in_landing_page(self):
        carousel_title_1 = 'carousel_1'
        carousel_title_2 = 'carousel_2'
        carousel_1 = CarouselHeaderF.create(
            title=carousel_title_1,
            order=0
        )
        carousel_2 = CarouselHeaderF.create(
            title=carousel_title_2,
            order=1
        )
        partner_name_1 = 'partner_name_1'
        partner_name_2 = 'partner_name_2'
        partner_1 = PartnerF.create(
            name=partner_name_1,
            order=0
        )
        partner_2 = PartnerF.create(
            name=partner_name_2,
            order=0
        )
        CustomThemeF.create(
            carousels=[carousel_1, carousel_2],
            partners=[partner_1, partner_2]
        )
        response = self.client.get(
            '/'
        )
        rendered_content = response.rendered_content
        self.assertEqual(
            carousel_title_1, response.context_data['headers'][0]['title'])
        self.assertIn(partner_name_1, rendered_content)
        self.assertTrue(
            rendered_content.index(partner_name_2) >
            rendered_content.index(partner_name_1)
        )

        # Test change orders of carousel and partners
        carousel_1.order = 1
        carousel_2.order = 0
        carousel_1.save()
        carousel_2.save()
        partner_1.order = 1
        partner_2.order = 0
        partner_1.save()
        partner_2.save()
        response = self.client.get(
            '/'
        )
        rendered_content = response.rendered_content
        self.assertEqual(
            carousel_title_1, response.context_data['headers'][1]['title'])
        self.assertTrue(
            rendered_content.index(partner_name_1) >
            rendered_content.index(partner_name_2)
        )
