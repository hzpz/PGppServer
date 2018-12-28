import time
import unittest

from location_provider import LocationProvider, SizeExceededError


class LocationProviderTest(unittest.TestCase):

    def test_missing_gets_next_location(self):
        location_provider = LocationProvider('location_provider_test.csv', 1)
        location = location_provider['0123456789']
        self.assertEqual(location['latitude'], '52')
        self.assertEqual(location['longitude'], '13')
        self.assertEqual(location['name'], 'Niedergörsdorf')

    def test_exceeding_size_raises_error(self):
        location_provider = LocationProvider('location_provider_test.csv', 1)
        location = location_provider['1111111111']
        with self.assertRaises(SizeExceededError): location = location_provider['2222222222']

    def test_locations_repeat(self):
        location_provider = LocationProvider('location_provider_test.csv', 1)
        location = location_provider['0123456789']
        self.assertEqual(location['name'], 'Niedergörsdorf')
        time.sleep(1)
        location = location_provider['0123456789']
        self.assertEqual(location['name'], 'Niedergörsdorf')


if __name__ == '__main__':
    unittest.main()
