import time
import unittest

from location_provider import LocationProvider, SizeExceededError


class LocationProviderTest(unittest.TestCase):

    def test_missing_gets_next_location(self):
        locations = [
            {
                "latitude": 52,
                "longitude": 13,
                "name": 'Niedergörsdorf'
            }
        ]
        location_provider = LocationProvider(locations, 1)
        location = location_provider['0123456789']
        self.assertEqual(location['latitude'], 52)
        self.assertEqual(location['longitude'], 13)
        self.assertEqual(location['name'], 'Niedergörsdorf')

    def test_exceeding_size_raises_error(self):
        location_provider = LocationProvider([{}], 1)
        location = location_provider['0123456789']
        with self.assertRaises(SizeExceededError): location = location_provider['9876543210']

    def test_locations_repeat(self):
        locations = [
            {
                "name": 'Location 1'
            },
            {
                "name": 'Location 2'
            }
        ]
        location_provider = LocationProvider(locations, 1)
        location = location_provider['0123456789']
        self.assertEqual(location['name'], 'Location 1')
        time.sleep(1)
        location = location_provider['0123456789']
        self.assertEqual(location['name'], 'Location 2')
        time.sleep(1)
        location = location_provider['0123456789']
        self.assertEqual(location['name'], 'Location 1')


if __name__ == '__main__':
    unittest.main()
