import logging
from cachetools import TTLCache
from threading import Lock

log = logging.getLogger('LocationProvider')


class LocationProvider(TTLCache):

    def __init__(self, locations, ttl):
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
        log.info('Current location for "%s": %s (%s, %s)',
                 key, location['name'], location['latitude'], location['longitude'])
        return location

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
