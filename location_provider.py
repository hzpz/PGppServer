import csv
import os.path
import logging
from cachetools import TTLCache
from threading import Lock

log = logging.getLogger('LocationProvider')


class LocationProvider(TTLCache):

    def __init__(self, locations_csv_filename, ttl):
        locations = self._get_locations(locations_csv_filename)
        super().__init__(len(locations), ttl)
        self.locations = LocationProvider.Locations(locations)
        self.lock = Lock()

    def __missing__(self, key):
        if self.currsize == self.maxsize:
            raise SizeExceededError(self.maxsize)
        self.lock.acquire()
        location = self.locations.next()
        self[key] = location
        self.lock.release()
        log.info('(%s) Current location: %s (%s, %s)',
                 key, location['name'], location['latitude'], location['longitude'])
        return location

    @staticmethod
    def _get_locations(locations_csv_filename):
        if not os.path.exists(locations_csv_filename):
            raise IOError('Unable to find CSV file with locations: %s' % locations_csv_filename)

        locations_from_csv = []
        with open(locations_csv_filename, newline='') as locations_file:
            reader = csv.reader(locations_file)
            for row in reader:
                if len(row) < 2 or len(row) > 3:
                    log.error('Ignoring CSV line with wrong format: %s', row)
                    continue

                locations_from_csv.append(
                    {
                        "latitude": row[0],
                        "longitude": row[1],
                        "name": row[2] if len(row) == 3 else 'Unknown'
                    })

        if not locations_from_csv:
            raise IOError(
                'CSV file with locations was empty or invalid: %s' % locations_csv_filename)

        log.info('Read %s location(s) from CSV file', len(locations_from_csv))
        return locations_from_csv

    class Locations:

        def __init__(self, locations):
            self.locations = locations
            self.currentLocationIndex = 0

        def next(self):
            locations = self.locations[self.currentLocationIndex]
            self.currentLocationIndex += 1
            if self.currentLocationIndex >= len(self.locations):
                self.reset()
            return locations

        def reset(self):
            self.currentLocationIndex = 0


class SizeExceededError(Exception):
    def __init__(self, maxsize):
        super().__init__(self, 'Exceeded size: %s' % maxsize)
