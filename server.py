import sys

import csv
import json
import logging
import os.path
import requests
import schedule
import threading
import time
from bottle import post, run, request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Configuration
host = '0.0.0.0'
port = 7477
min_raid_level = 3
webhook_url = 'http://localhost:4000'
teleport_delay_minutes = 1
locations_csv_filename = 'locations.csv'
seen_raids_filename = 'seen.cache'
# /Configuration

logging.basicConfig(
    format='%(asctime)s %(levelname)-5s [%(name)-22.22s] %(message)s',
    level=logging.INFO
)
log = logging.getLogger('PGppServer')

seen_raids = {}
locations = []
current_location = {}
current_location_index = 0
executor = ThreadPoolExecutor(max_workers=2)
pokemon_names = {}
move_names = {}
team_names = {}


@post('/loc')
def loc():
    return {
        "lat": current_location['latitude'],
        "lng": current_location['longitude'],
        "latitude": current_location['latitude'],
        "longitude": current_location['longitude']
    }


@post('/data')
def data():
    pg_data = request.json
    for gym in pg_data['gyms']:
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

            executor.submit(publish, raid)


def publish(raid):
    log.info('Publishing egg/raid to webhook...')
    send_to_webhook(raid)
    mark_seen(raid)


def has_raid(gym):
    return gym['raidLevel'] >= min_raid_level


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
    requests.post(webhook_url, json=[{
        "type": "raid",
        "message": raid
    }])


def get_locations():
    if not os.path.exists(locations_csv_filename):
        log.error('Unable to find CSV file with locations: %s', locations_csv_filename)
        sys.exit(1)

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

    if len(locations_from_csv) == 0:
        log.error('CSV file with locations was empty or invalid: %s', locations_csv_filename)
        sys.exit(1)

    log.info('Read %s location(s) from CSV file', len(locations_from_csv))
    return locations_from_csv


def change_location():
    global locations, current_location_index
    current_location_index += 1
    if current_location_index >= len(locations):
        current_location_index = 0
    set_current_location()


def set_current_location():
    global locations, current_location, current_location_index
    current_location = locations[current_location_index]
    log.info('Current location: %s (%s, %s)',
             current_location['name'], current_location['latitude'], current_location['longitude'])


def continuously_run_scheduler():
    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while True:
                schedule.run_pending()
                time.sleep(1)

    continuous_thread = ScheduleThread()
    continuous_thread.setDaemon(True)
    continuous_thread.start()


def load_seen_raids():
    if not os.path.exists(seen_raids_filename):
        return {}

    with open(seen_raids_filename) as seen_file:
        seen_json = json.loads(seen_file.read())
        log.debug('Loaded %s seen raids', len(seen_json))
        return seen_json


def save_seen_raids(seen_dict):
    seen_json = json.dumps(seen_dict, indent=1)
    with open(seen_raids_filename, 'w') as seen_file:
        seen_file.write(seen_json)
    log.debug('Saved %s seen raids', len(seen_dict))


def schedule_teleports(delay):
    schedule.every(delay).minutes.do(change_location)
    continuously_run_scheduler()


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
    set_current_location()
    schedule_teleports(teleport_delay_minutes)
    seen_raids = load_seen_raids()
    load_human_readable_names()
    run(host=host, port=port, quiet=True)

    log.info('Stopping PGppServer...')
    save_seen_raids(seen_raids)
