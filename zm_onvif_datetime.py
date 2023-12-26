#!/usr/bin/env python
"""
ZoneMinder ONVIF camera date/time setter

https://github.com/jantman/zondeminder-onvif-date-time-setter
"""

import sys
import os
import argparse
import logging
from urllib.parse import urljoin, urlparse
from typing import Dict
import importlib.resources
from datetime import datetime, timezone

import requests
from onvif import ONVIFCamera

logging.basicConfig(
    level=logging.WARNING,
    format="[%(asctime)s %(levelname)s] %(message)s"
)
logger: logging.Logger = logging.getLogger()

for lname in ['urllib3', 'zeep']:
    l = logging.getLogger(lname)
    l.setLevel(logging.WARNING)
    l.propagate = True


class ZmOnvifDateTimeSetter:

    def __init__(self, dry_run: bool = False):
        self.dry_run: bool = dry_run
        self.wsdl_dir: str = os.path.abspath(
            importlib.resources.files('onvif') / '..' / 'wsdl'
        )
        logger.debug('WSDL directory: %s', self.wsdl_dir)
        try:
            self.zm_url: str = os.environ['ZM_API_URL']
        except KeyError:
            raise RuntimeError(
                'ERROR: Please set ZM_API_URL environment variable'
            )
        if not self.zm_url.endswith('/'):
            self.zm_url += '/'
        try:
            self.onvif_user: str = os.environ['ONVIF_USERNAME']
        except KeyError:
            raise RuntimeError(
                'ERROR: Please set ONVIF_USERNAME environment variable'
            )
        try:
            self.onvif_pass: str = os.environ['ONVIF_PASSWORD']
        except KeyError:
            raise RuntimeError(
                'ERROR: Please set ONVIF_PASSWORD environment variable'
            )
        logger.debug(
            'Using ZoneMinder API URL: %s; ONVIF username=%s password=%s',
            self.zm_url, self.onvif_user, '*' * len(self.onvif_pass)
        )
        now: datetime = datetime.now(timezone.utc).astimezone()
        self.tz_str: str = now.strftime('GMT%:z')
        logger.info('Using local timezone: %s', self.tz_str)

    def run(self, fail_fast: bool = False):
        monitors: Dict[str, str] = self._list_monitors()
        logger.debug('Got %d monitors: %s', len(monitors), monitors)
        failed: int = 0
        success: int = 0
        for mon_id, host in sorted(monitors.items()):
            try:
                self._handle_camera(mon_id, host)
                success += 1
            except Exception as ex:
                if fail_fast:
                    raise
                logger.error(
                    'Monitor %s (%s) failed: %s', mon_id, host, ex,
                    exc_info=True
                )
                failed += 1
        if not failed:
            logger.info(
                'Successfully set date and time on all %d monitors',
                success
            )
            return
        logger.error(
            'Set date and time on %d monitors; %d failed', success, failed
        )
        raise SystemExit(failed)

    def _handle_camera(self, mon_id: str, host: str):
        logger.info(
            'Handling monitor %s - hostname=%s',mon_id, host
        )
        cam: ONVIFCamera = ONVIFCamera(
            host=host, port=80, user=self.onvif_user, passwd=self.onvif_pass,
            wsdl_dir=self.wsdl_dir
        )
        hostname: str = cam.devicemgmt.GetHostname().Name
        logger.debug('Connected to camera with hostname %s', hostname)
        cam_dt: dict = cam.devicemgmt.GetSystemDateAndTime()
        logger.debug('Camera GetSystemDateAndTime(): %s', cam_dt)
        dt: datetime = self._onvif_dict_to_utc_datetime(cam_dt)
        utcnow: datetime = datetime.now(timezone.utc)
        delta: int = int(abs(dt.timestamp() - utcnow.timestamp()))
        if delta < 60:
            logger.info(
                'Monitor %s (%s) system date/time of %s is %d seconds '
                'from now; do not update',mon_id, host, dt, delta
            )
            return
        logger.info(
            'Monitor %s (%s) system date/time of %s is %d seconds '
            'from now; updating', mon_id, host, dt, delta
        )
        time_params = {
            'DateTimeType': 'Manual',
            'DaylightSavings': False,
            'TimeZone': {
                'TZ': self.tz_str
            },
            'UTCDateTime': {
                'Time': {
                    'Hour': utcnow.hour,
                    'Minute': utcnow.minute,
                    'Second': utcnow.second
                },
                'Date': {
                    'Year': utcnow.year,
                    'Month': utcnow.month,
                    'Day': utcnow.day
                }
            }
        }
        if self.dry_run:
            logger.warning(
                'DRY RUN: Would call SetSystemDateAndTime with params: %s',
                time_params
            )
            return
        logger.debug('Call SetSystemDateAndTime with params: %s', time_params)
        cam.devicemgmt.SetSystemDateAndTime(time_params)
        logger.info('Updated date/time on Monitor %s (%s)', mon_id, host)

    def _onvif_dict_to_utc_datetime(self, d: dict) -> datetime:
        return datetime(
            year=d['UTCDateTime']['Date']['Year'],
            month=d['UTCDateTime']['Date']['Month'],
            day=d['UTCDateTime']['Date']['Day'],
            hour=d['UTCDateTime']['Time']['Hour'],
            minute=d['UTCDateTime']['Time']['Minute'],
            second=d['UTCDateTime']['Time']['Second'],
            tzinfo=timezone.utc
        )

    def _list_monitors(self) -> Dict[str, str]:
        url: str = urljoin(self.zm_url, 'monitors.json')
        logger.debug('GET %s', url)
        r = requests.get(url)
        logger.debug('Got HTTP %d: %s', r.status_code, r.text)
        r.raise_for_status()
        res = {}
        for row in r.json()['monitors']:
            res[row['Monitor']['Id']] = urlparse(row['Monitor']['Path']).hostname
        return res


def parse_args(argv):
    p = argparse.ArgumentParser(description='ZM ONVIF Date/Time Setter')
    p.add_argument(
        '-v', '--verbose', dest='verbose', action='store_true',
        default=False, help='verbose output'
    )
    p.add_argument(
        '-f', '--fail-fast', dest='fail_fast', action='store_true',
        default=False, help='Exit on first error instead of trying all cameras'
    )
    p.add_argument(
        '-D', '--dry_run', dest='dry_run', action='store_true',
        default=False, help='Log what would be done but do not change anything'
    )
    args = p.parse_args(argv)
    return args


def set_log_info(l: logging.Logger):
    """set logger level to INFO"""
    set_log_level_format(
        l,
        logging.INFO,
        '%(asctime)s %(levelname)s:%(name)s:%(message)s'
    )


def set_log_debug(l: logging.Logger):
    """set logger level to DEBUG, and debug-level output format"""
    set_log_level_format(
        l,
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s"
    )


def set_log_level_format(lgr: logging.Logger, level: int, fmt: str):
    """Set logger level and format."""
    formatter = logging.Formatter(fmt=fmt)
    lgr.handlers[0].setFormatter(formatter)
    lgr.setLevel(level)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose:
        set_log_debug(logger)
    else:
        set_log_info(logger)

    ZmOnvifDateTimeSetter(dry_run=args.dry_run).run(fail_fast=args.fail_fast)
