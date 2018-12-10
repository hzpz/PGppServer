import sys
import time

import csv
import json
import logging
import os.path
from queue import Queue
from threading import Thread
from datetime import datetime
import requests
from bottle import post, run, request, response

from location_provider import LocationProvider, SizeExceededError

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
pokemon_names = {}
move_names = {}
team_names = {}


@post('/loc')
def loc():
    global location_provider
    loc_data = request.json
    device_uuid = loc_data.get('uuid')
    try:
        location = location_provider[device_uuid]
    except SizeExceededError:
        error_message = '"%s" exceeds device limit, already got: %s' % device_uuid, list(
            location_provider.keys())
        log.error(error_message)
        response.status = 400
        return {
            "error": error_message
        }

    return {
        "lat": location['latitude'],
        "lng": location['longitude'],
        "latitude": location['latitude'],
        "longitude": location['longitude']
    }


@post('/data')
def data():
    global pokemon_names, move_names
    pg_data = request.json
    for gym in get_unique_gyms(pg_data):
        if has_raid(gym):
            raid = parse_raid(gym)
            log.debug('Raw raid: %s', raid)

            if seen(raid):
                log.debug('Already seen raid at %s', raid['gym_id'])
                continue

            if raid['pokemon_id']:
                log.info('Found %s raid (%s/%s) at %s running until %s',
                         pokemon_names[raid['pokemon_id']],
                         move_names[raid['move_1']], move_names[raid['move_2']],
                         raid['gym_id'], datetime.fromtimestamp(raid['end']).strftime('%H:%M'))
            else:
                log.info('Found level %s egg at %s starting at %s',
                         raid['level'], raid['gym_id'],
                         datetime.fromtimestamp(raid['start']).strftime('%H:%M'))

            enqueue(raid)


def get_unique_gyms(pg_data):
    gyms = pg_data.get('gyms') or []
    unique_gyms = list({gym['gym_id']: gym for gym in gyms}.values())
    if len(gyms) != len(unique_gyms):
        log.debug('Received %s duplicate gym(s)', len(gyms) - len(unique_gyms))
    return unique_gyms


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


def get_locations():
    if not os.path.exists(LOCATIONS_CSV_FILENAME):
        log.error('Unable to find CSV file with locations: %s', LOCATIONS_CSV_FILENAME)
        sys.exit(1)

    locations_from_csv = []
    with open(LOCATIONS_CSV_FILENAME, newline='') as locations_file:
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
        log.error('CSV file with locations was empty or invalid: %s', LOCATIONS_CSV_FILENAME)
        sys.exit(1)

    log.info('Read %s location(s) from CSV file', len(locations_from_csv))
    return locations_from_csv


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


def load_human_readable_names():
    global pokemon_names, move_names, team_names
    with open('en.json') as names_file:
        names = json.loads(names_file.read())

    # Pokemon ID -> Name
    pokemon = names.get("pokemon", {})
    for id_, val in pokemon.items():
        pokemon_names[int(id_)] = pokemon.get(id_, val)

    # Move ID -> Name
    moves = names.get("moves", {})
    for id_, val in moves.items():
        move_names[int(id_)] = moves.get(id_, val)

    # Team ID -> Name
    teams = names.get("teams", {})
    for id_, val in teams.items():
        team_names[int(id_)] = teams.get(id_, val)

    log.debug('Loaded %s pokémon, %s moves and %s teams',
              len(pokemon_names), len(move_names), len(team_names))


if __name__ == '__main__':
    log.info('Starting PGppServer...')
    locations = get_locations()
    location_provider = LocationProvider(locations, TELEPORT_DELAY_MINUTES * 60)
    publish_thread = Thread(target=publish_raids)
    publish_thread.start()
    seen_raids = load_seen_raids()
    load_human_readable_names()
    run(host=HOST, port=PORT, quiet=True)

    log.info('Stopping PGppServer...')
    publish_queue.put(None)
    save_seen_raids(seen_raids)
