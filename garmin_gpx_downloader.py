#!/usr/bin/env python3

import logging
import argparse
import math
import traceback
from pathlib import Path
from datetime import datetime 
from garminconnect import Garmin
from helpers import *

# Activities that should be skipped 
ACTIVITY_TYPES_TO_SKIP = ['breathwork']

# Suppress garminconnect library logging to avoid tracebacks in normal operation
logging.getLogger("garminconnect").setLevel(logging.CRITICAL)

# Create global logger instance for this file
logger = logging.getLogger(__name__)

def is_within_radius(base_lat: float, base_long: float, act_lat: float, act_long: float, 
                     radius_km: float) -> bool:
    """
    Returns True if (act_lat, act_long) is within radius_km of
    (base_lat, base_long), otherwise False.
    """

    # Earth radius in kilometers
    EARTH_RADIUS_KM = 6371.0

    # Convert degrees to radians
    lat1 = math.radians(base_lat)
    lon1 = math.radians(base_long)
    lat2 = math.radians(act_lat)
    lon2 = math.radians(act_long)

    # Differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = (
        math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = EARTH_RADIUS_KM * c

    return distance <= radius_km

def get_activity_id(a: dict) -> str:
    """
    Return the activity Id 
    """
    return a['activityId']

def get_all_activities(api: Garmin) -> list[dict]:
    """
    Return a list with all activities recorded on the Garmin account.
    """
    logger.debug("Fetching all activities.")
    amt_activities = api.count_activities()
    logger.debug(f"{amt_activities} activity_count found.")

    activities = []
    logger.debug(f"Fetching {amt_activities} activities...")
    activities = api.get_activities(0, amt_activities)
    logger.debug(f"Fetched {len(activities)} activities")
    if type(activities) == list:
        return activities
    elif type(activities) == dict:
        return [activities]
    else:
        logger.critical("Something went wrong fetching all activities.")
        exit(1)

def get_name(a: dict) -> str:
    """
    Returns the activity name with spaces replaced by underscores
    """
    return a['activityName'].replace(' ', '_')

def get_id(a: dict) -> str:
    """
    Returns the activity Id
    """
    return a['activityId']

def get_type(a: dict) -> str:
    """
    Return the activity type
    """
    return a['activityType']['typeKey']

def get_start_coordinate(a: dict) -> tuple[float, float]:
    """
    Return the acitivity coordinate as a (latitude, longitude) tuple
    """
    return a['startLatitude'], a['startLongitude']

def get_timestamp(a: dict) -> str:
    """
    Returns the activity timestamp as "YEAR_MONTH_DAY_HOUR_MINUTE"
    """
    MS_PER_SECOND = 1000
    timestamp = datetime.fromtimestamp(a['beginTimestamp']/MS_PER_SECOND)
    date = f"{timestamp.year :04d}_{timestamp.month  :02d}_{timestamp.day :02d}"
    time = f"{timestamp.hour :02d}_{timestamp.minute :02d}"
    return date + '_' + time

def get_gpx(api: Garmin, a: dict) -> str:
    """
    Return the GPX data as a string from an activity.
    """
    run_gpx_bytes = api.download_activity(get_id(a), Garmin.ActivityDownloadFormat.GPX)
    return run_gpx_bytes.decode("utf-8")

def write_gpx_file(filename: str, gpx_data, path='./gpx_files/'):
    """
    Write the GPX data string to 'path/filename'
    """
    # Create directory for GPX files 
    Path(path).mkdir(parents=True, exist_ok=True)

    logger.debug(f"Writing file {path}{filename}")
    try:
        with open(f"{path}{filename}", "x") as f:
            f.write(gpx_data)
    except FileExistsError:
        logger.debug(f"File {path}{filename} already exists, skipping it!")
        pass

def write_activity_gpx(api: Garmin, a: dict) -> None:
    """
    Fetch the GPX data from certain activity from the api, and write the gpx data to a file
    """
    gpx = get_gpx(api, a)
    filename = get_name(a) + get_timestamp(a) + ".gpx"
    write_gpx_file(filename, gpx)

def activity_has_valid_name(a: dict, names: list[str] | None) -> bool:
    """
    Return true if no names are specified
    Return true if one of the names is present in the activity name.
    Ignores capitals
    """
    if names == None:
        return True
    activity_name = get_name(a).lower()
    for n in names:
        if n.lower() in activity_name:
            return True
    return False

def activity_has_valid_type(a: dict, types: list[str] | None) -> bool:
    """
    Return true if no activity types are specified
    Return true if the activity is present in the valid activity types.
    Return false if the activity is in the ACTIVITY_TYPES_TO_SKIP
    """
    if types == None:
        return True
    for t in types:
        if t in get_type(a):
            return True
    return False

def parse_coordinate_argument(c: str) -> tuple[float, float]:
    """
    Parse a coordinate of form: 
    (latitude, longitude) 
    and return both values as a tuple.
    """
    logger.debug(f"Parse coordinate string: {c}")
    c = c.strip()
    cLat, cLong = c[1:-1].split(',')
    return float(cLat), float(cLong)

def activity_start_within_radius(a: dict, c: tuple[float, float], r: float | None) -> bool:
    """
    Return true if no radius is specified (filter not used)
    Return true if the activity start location is within the radius r of the given coordinate.
    """
    if r == None:
        return True
    aLatitude, aLongitude = get_start_coordinate(a)

    return is_within_radius(c[0], c[1], aLatitude, aLongitude, r)

def is_valid_activity(a: dict, args: argparse.Namespace) -> bool:
    """
    Return true if the activity is valid according to the name, type and radius filter (and according to the specified filter combination operator 'OR'/'AND')
    Return false otherwise
    """
    if get_type(a) in ACTIVITY_TYPES_TO_SKIP:
        logger.debug("Skip activity type")
        return False
    and_operator = args.filtertype == 'and' and (
        activity_has_valid_name(a, args.name) and \
        activity_has_valid_type(a, args.activity_type) and \
        activity_start_within_radius(a, args.start_coordinate, args.radius))
    or_operator = args.filtertype == 'or' and (
        activity_has_valid_name(a, args.name) or \
        activity_has_valid_type(a, args.activity_type) or \
        activity_start_within_radius(a, args.start_coordinate, args.radius))
    return and_operator or or_operator

def filter_activities(activities: list[dict], args: argparse.Namespace) -> list[dict]:
    """
    Filter all activities based on the passed filter arguments
    Returns all activities that check all passed filter arguments
    """
    logger.info(f"Filtering {len(activities)} activities.")
    filtered = []
    for a in activities:
        logger.debug(f"Filtering activityId: {get_activity_id(a)} with activityType: {get_type(a)} and Name: {get_name(a)}")
        if is_valid_activity(a, args):
            filtered.append(a)
        else:
            logger.debug(f"Activity {get_name(a)} filtered out")

    logger.info(f"After filtering, {len(filtered)} activities left over")
    return filtered

def get_last_activity_coordinate(api: Garmin) -> tuple[float, float]:
    """
    Return the coordinate from the last recorded activity
    """
    logger.debug(f"Parsing coordinate from last activity.")
    # TODO: What if last doesn't have a start coordinate --> assume user not stupid
    last_activity = api.get_last_activity()
    if not last_activity:
        print('No start coordinate is provided and fetching last activity failed')
        exit(1)
    return get_start_coordinate(last_activity)


def format_arguments(api: Garmin, args: argparse.Namespace) -> argparse.Namespace:
    """
    Format user provided arguments to a format that the rest of the script anticipates on
    """
    # If a radius was specified
    if args.radius:
        args.radius = float(args.radius)
        # If a start coordinate was not provided, change the start coordinate to 'the start coordinate of the last activity'
        if not args.start_coordinate:
            args.start_coordinate = get_last_activity_coordinate(api)
            # If a start coordinate was provided, parse it
        elif args.start_coordinate:
            args.start_coordinate = parse_coordinate_argument(args.start_coordinate)
        logger.debug(f"Parsed coordinate argument: {args.start_coordinate}")
    return args

def main(args: argparse.Namespace) -> None:
    if args.start_coordinate and not args.radius:
        parser.error("Providing a start coordinate argument requires a radius argument to be specified.")

    # Initialize API with authentication (will only prompt for credentials if needed)
    api = init_api()

    if not api:
        print("❌ Failed to initialize API. Exiting.")
        return

    activities = get_all_activities(api)
    print(f"\nIn total {len(activities)} activities found.")
    # If there is a filter specified, filter the activities
    if (args.name or args.activity_type or args.radius):
        args = format_arguments(api, args)
        logger.info(f"Filtering on:\n\t\tName: {args.name}\n\t\tType: {args.activity_type}\n\t\tRadius: {args.radius}\n\t\tCoordinate: {args.start_coordinate}")
        activities = filter_activities(activities, args)
        print(f"\nAfter filtering, {len(activities)} activities left over.")

    if not args.nowrite:
        print("\nFetching data and writing to GPX files.\nThis may take a while...\n")
        for i in range(len(activities)):
            print(f"Writing file {i+1 :4d} out of {len(activities) :4d}")
            write_activity_gpx(api, activities[i])

def setLogger(level: str) -> None:
    """
    Set the logger and handler appropriately with the provided loglevel
    """
    # Don't propagate the logging to submodules
    logger.propagate = False
    loglevel = eval("logging." + level)
    logger.setLevel(loglevel)
    # Handler propagates the logging to stdout
    handler = logging.StreamHandler()
    handler.setLevel(loglevel)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    print(f"Logging to stdout with loglevel {logging.getLevelName(logger.getEffectiveLevel())}\n")

def create_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog = 'Garmin_GPX_Downloader',
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description = '''
        This program downloads the GPX files from your activities in GarminConnect.
        Filters can be applied to only take GPX files:
        - With certain text strings in the activity name (-n).
            NOTE: When multiple strings are provided, every activity_name that contains any of the provided strings will be kept (and thus further processed)
        - With certain activity types (-t)
        - Within a certain radius (-r) of the start location from your last recorded activity
        - Within a certain radius (-r) of a specified start location coordinate (-c)
        Or any AND/OR combination (-f) of the above!
        ''',
    )
    parser.add_argument(
        '-l',
        '--loglevel',
        default = 'CRITICAL',
        required=False,
        choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help = '''Specify the loglevel, default CRITICAL.'''
    )
    parser.add_argument(
        '-n',
        '--name',
        nargs='+',
        help = '''Specify an activity name to filter on. If you specify an activity name, it will only fetch activities that have the "name" as substring. Ignores capitals.'''
    )
    parser.add_argument(
        '-t',
        '--activity_type',
        nargs='+',
        help = '''Specify an activity type to filter on. This will make sure only activities with the specified activity type will be processed. Examples ["cycling", "running", "walking"]'''
    )
    parser.add_argument(
        '-c',
        '--start_coordinate',
        help = '''Provide a coordinate pair in format "(latitude,longitude)" brackets included. This coordinate will be used as the circle center for filtering all activities within a certain range of a start location.'''
    )
    parser.add_argument(
        '-r',
        '--radius',
        required = 'start_coordinate' in sys.argv, #Only required if a start coordinate is provided
        help = '''Specify a radius in km.
        This filters all activities on whether "the start location of the activity is within the km range of your start coordinate".
        NOTE: if you don\'t specify a start coordinate (using the -s or --start_coordinate flag), then the start coordinate of your last recorded activity will be used.'''
    )
    parser.add_argument(
        '-f',
        '--filtertype',
        required = False,
        default = 'and',
        choices = ['or', 'and'],
        help= '''Specify whether you want to combine multiple filters using the "OR" or the "AND" operation. This will result in:
                                (validType OR validName OR withinRadius) vs.
                                (validType AND validName AND withinRadius)
            '''
    )
    parser.add_argument(
        '--nowrite',
        action = 'store_true',
        help = '''[DEBUG] Dry-run without fetching & writing the GPXs to file yet'''
    )
    return parser

if __name__ == "__main__":
    parser = create_arg_parser()
    args = parser.parse_args() 
    setLogger(args.loglevel)
    logger.debug(f"Starting main with args {args}")

    try:
        main(args)
    except KeyboardInterrupt:
        print("\n\n🚪 Exiting due to user interrupt. Goodbye! 👋")
    except Exception as e:
        print(traceback.format_exc())
        print(f"\n❌ Unexpected error: {e}")
