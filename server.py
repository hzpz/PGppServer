import sys
import time

import base64
import json
import logging
import os.path
from queue import Queue
from threading import Thread
from datetime import datetime
import requests
from bottle import post, run, request, response

from location_provider import LocationProvider, SizeExceededError
from pogoprotos.enums.pokemon_id_pb2 import PokemonId
from pogoprotos.enums.pokemon_move_pb2 import PokemonMove
from pogoprotos.map.fort.fort_type_pb2 import FortType
from pogoprotos.networking.responses.get_map_objects_response_pb2 import GetMapObjectsResponse

# Configuration
HOST = 'localhost'
PORT = 7477
MIN_RAID_LEVEL = 1
WEBHOOK_URL = 'http://localhost:4000'
TELEPORT_DELAY_MINUTES = 1
LOCATIONS_CSV_FILENAME = 'locations.csv'
SEEN_RAIDS_FILENAME = 'seen.cache'
# /Configuration

logging.basicConfig(
    format='%(asctime)s %(levelname)-7s [%(name)-10.10s] %(message)s',
    level=logging.INFO
)
log = logging.getLogger('PGppServer')

seen_raids = {}
location_provider = None
publish_queue = Queue()


@post('/loc')
def loc():
    global location_provider
    loc_data = request.json

    if not loc_data:
        log.error('Body was empty or invalid: %s', request.body.read())
        return http_400('Body was empty or invalid')

    device_uuid = loc_data.get('uuid')
    try:
        location = location_provider[device_uuid]
    except SizeExceededError:
        log.error('"%s" exceeds device limit, already got: %s',
                  device_uuid, list(location_provider.keys()))
        return http_400('Exceeded device limit')

    return {
        "lat": location['latitude'],
        "lng": location['longitude'],
        "latitude": location['latitude'],
        "longitude": location['longitude']
    }


@post('/data')
def data():
    pg_data = request.json

    if not pg_data:
        log.error('Body was empty or invalid: %s', request.body.read())
        return http_400('Body was empty or invalid')

    for gym in get_unique_gyms(pg_data):
        if has_raid(gym):
            raid = parse_raid(gym)
            log.debug('Raw raid: %s', raid)

            if seen(raid):
                log.debug('Already seen raid at %s', raid['gym_id'])
                continue

            if raid['pokemon_id']:
                log.info('Found %s raid (%s/%s) at %s running until %s',
                         PokemonId.Name(raid['pokemon_id']),
                         PokemonMove.Name(raid['move_1']), PokemonMove.Name(raid['move_2']),
                         raid['gym_id'], datetime.fromtimestamp(raid['end']).strftime('%H:%M'))
            else:
                log.info('Found level %s egg at %s starting at %s',
                         raid['level'], raid['gym_id'],
                         datetime.fromtimestamp(raid['start']).strftime('%H:%M'))

            enqueue(raid)


def http_400(error_message):
    response.status = 400
    return {
        "error": error_message
    }


def get_unique_gyms(pg_data):
    if 'gym' in pg_data:
        gyms = pg_data.get('gyms')
        unique_gyms = list({gym['gym_id']: gym for gym in gyms}.values())
        if len(gyms) != len(unique_gyms):
            log.debug('Received %s duplicate gym(s)', len(gyms) - len(unique_gyms))
        return unique_gyms
    elif 'protos' in pg_data:
        protos = pg_data.get('protos')
        gyms = []
        for proto in protos:
            log.debug('Raw proto: %s', proto)
            if 'GetMapObjects' in proto:
                gmoString = proto.get('GetMapObjects')
                gmo = GetMapObjectsResponse()
                gmo.ParseFromString(base64.b64decode(gmoString))
                for map_cell in gmo.map_cells:
                    for fort in map_cell.forts:
                        if fort.type is not FortType.Value('GYM'):
                            continue

                        gyms.append(parse_fort(fort))
        return gyms
    else:
        return []


def parse_fort(fort):
    gym = {
        'gym_id': fort.id,
        'team': fort.owned_by_team,
        'latitude': fort.latitude,
        'longitude': fort.longitude,
        'raidLevel': 0,
        'raidSpawnMs': 0,
        'raidBattleMs': 0,
        'raidEndMs': 0,
        'raidPokemon': 0,
        'cp': 0,
        'move1': 0,
        'move2': 0
    }

    if fort.raid_info:
        raid_info = fort.raid_info
        gym.update({
            'raidLevel': raid_info.raid_level,
            'raidSpawnMs': raid_info.raid_spawn_ms,
            'raidBattleMs': raid_info.raid_battle_ms,
            'raidEndMs': raid_info.raid_end_ms
        })

        if raid_info.raid_pokemon:
            raid_pokemon = raid_info.raid_pokemon
            gym.update({
                'raidPokemon': raid_pokemon.pokemon_id,
                'cp': raid_pokemon.cp,
                'move1': raid_pokemon.move_1,
                'move2': raid_pokemon.move_2
            })
    return gym


def enqueue(raid):
    global publish_queue
    publish_queue.put(raid)


def publish_raids():
    global publish_queue
    while True:
        raid = publish_queue.get()
        if not raid:
            break
        if seen(raid):
            log.warning('Already published raid at %s', raid['gym_id'])
            continue
        log.debug('Publishing egg/raid to webhook...')
        send_to_webhook(raid)
        mark_seen(raid)
        publish_queue.task_done()


def has_raid(gym):
    return gym['raidLevel'] >= MIN_RAID_LEVEL


def is_active(raid):
    return raid['pokemon_id'] is not None


def seen(raid):
    global seen_raids
    if raid['gym_id'] not in seen_raids:
        return False

    if is_active(raid):
        return seen_raids[raid['gym_id']] == raid['start']
    else:
        return seen_raids[raid['gym_id']] == raid['spawn']


def mark_seen(raid):
    global seen_raids
    if is_active(raid):
        seen_raids.update({raid['gym_id']: raid['start']})
    else:
        seen_raids.update({raid['gym_id']: raid['spawn']})


def parse_raid(gym):
    raid_spawn = datetime_from_utc_to_local(parse_timestamp_in_millis(gym['raidSpawnMs']))
    raid_start = datetime_from_utc_to_local(parse_timestamp_in_millis(gym['raidBattleMs']))
    raid_end = datetime_from_utc_to_local(parse_timestamp_in_millis(gym['raidEndMs']))

    raid = {
        "gym_id": gym['gym_id'],
        "team_id": gym['team'],
        "latitude": gym['latitude'],
        "longitude": gym['longitude'],
        "spawn": raid_spawn.timestamp(),
        "start": raid_start.timestamp(),
        "end": raid_end.timestamp(),
        "level": gym['raidLevel'],
        "pokemon_id": None,
        "cp": None,
        "move_1": None,
        "move_2": None
    }

    raid_boss = gym['raidPokemon']
    if raid_boss != 0:
        raid.update({
            "pokemon_id": raid_boss,
            "cp": gym['cp'],
            "move_1": gym['move1'],
            "move_2": gym['move2']
        })

    return raid


def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset


def parse_timestamp_in_millis(timestamp_in_millis):
    return datetime.utcfromtimestamp(timestamp_in_millis / 1000)


def send_to_webhook(raid):
    requests.post(WEBHOOK_URL, json=[{
        "type": "raid",
        "message": raid
    }])


def load_seen_raids():
    if not os.path.exists(SEEN_RAIDS_FILENAME):
        return {}

    with open(SEEN_RAIDS_FILENAME) as seen_file:
        seen_json = json.loads(seen_file.read())
        log.debug('Loaded %s seen raids', len(seen_json))
        return seen_json


def save_seen_raids(seen_dict):
    seen_json = json.dumps(seen_dict, indent=1)
    with open(SEEN_RAIDS_FILENAME, 'w') as seen_file:
        seen_file.write(seen_json)
    log.debug('Saved %s seen raids', len(seen_dict))


if __name__ == '__main__':
    log.info('Starting PGppServer...')
    try:
        location_provider = LocationProvider(LOCATIONS_CSV_FILENAME, TELEPORT_DELAY_MINUTES * 60)
        publish_thread = Thread(target=publish_raids)
        publish_thread.start()
        seen_raids = load_seen_raids()
    except Exception as e:
        log.error('%s', e)
        sys.exit(1)

    run(host=HOST, port=PORT, quiet=True)

    log.info('Stopping PGppServer...')
    publish_queue.put(None)
    save_seen_raids(seen_raids)
