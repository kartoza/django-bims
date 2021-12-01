import logging
import os
import csv
from datetime import datetime

from django.test import TestCase
from bims.tests.model_factories import (
    LocationSiteF, LocationContextF, LocationContextGroupF, WaterTemperatureF
)
from bims.models.water_temperature import (
    get_thermal_zone,
    calculate_indicators,
    thermograph_data
)

logger = logging.getLogger('bims')
test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')


class TestThermalData(TestCase):

    def setUp(self):
        self.location_site = LocationSiteF.create()
        lcg = LocationContextGroupF.create(
            key='thermal_zone'
        )
        LocationContextF.create(
            site=self.location_site,
            group=lcg,
            value='upper'
        )
        thermal_data_file = os.path.join(
            test_data_directory, 'thermal_data_sample.csv')
        with open(thermal_data_file) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                if row.get('Date'):
                    WaterTemperatureF.create(
                        date_time=datetime.strptime(row.get('Date'), '%m/%d/%y'),
                        is_daily=True,
                        value=row.get('Mean'),
                        maximum=row.get('Max'),
                        minimum=row.get('Min'),
                        location_site=self.location_site
                    )

    def test_get_thermal_zone(self):
        zone = get_thermal_zone(self.location_site)
        self.assertEqual(zone, 'upper')

    def test_thermal_calculation(self):
        result = calculate_indicators(self.location_site, 2009)

        # Check with the result from xls
        self.assertEqual(round(result['annual']['annual_mean'], 2), 14.60)
        self.assertEqual(round(result['annual']['annual_range'], 2), 3.11)

        self.assertEqual(round(result['weekly']['weekly_mean_avg'], 2), 21.05)
        self.assertEqual(round(result['weekly']['weekly_min_avg'], 2), 8.75)
        self.assertEqual(round(result['weekly']['weekly_max_avg'], 2), 23.11)

        self.assertEqual(round(result['thirty_days']['thirty_max_avg'], 2),
                         22.78)
        self.assertEqual(round(result['thirty_days']['thirty_min_avg'], 2),
                         9.48)

        self.assertEqual(round(result['ninety_days']['ninety_max_avg'], 2),
                         22.78)
        self.assertEqual(round(result['ninety_days']['ninety_min_avg'], 2),
                         9.87)

        self.assertEqual(
            result['threshold']['weekly_mean'],
            70
        )
        self.assertEqual(
            result['threshold']['weekly_mean_dur'],
            54
        )
        self.assertEqual(
            result['threshold']['weekly_min'],
            166
        )
        self.assertEqual(
            result['threshold']['weekly_max'],
            0
        )
        self.assertEqual(
            result['threshold']['weekly_min_dur'],
            130
        )
        self.assertEqual(
            result['threshold']['weekly_max_dur'],
            0
        )

    def test_thermograph_calculation(self):
        annual_data = calculate_indicators(self.location_site, 2009, True)
        thermograph = thermograph_data(annual_data['weekly'])

        self.assertEqual(
            len(thermograph['95%_up']),
            len(annual_data['weekly']['weekly_mean_data']))

        self.assertEqual(
            round(thermograph['95%_low'][50], 2),
            16.0
        )
        self.assertEqual(
            round(thermograph['95%_up'][40], 2),
            22.80
        )
        self.assertEqual(
            round(thermograph['L95%_1SD'][290], 2),
            12.09
        )
        self.assertEqual(
            round(thermograph['U95%_1SD'][330], 2),
            20.72
        )
        self.assertEqual(
            round(thermograph['L95%_2SD'][60], 2),
            14.28
        )
        self.assertEqual(
            round(thermograph['U95%_2SD'][10], 2),
            24.48
        )
