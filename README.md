# zondeminder-onvif-date-time-setter

Python script (and Docker container) to connect to ZoneMinder API and set date/time on all monitors via ONVIF

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

## Description

This is a utility to set the date and time on IP camera ZoneMinder monitors that support ONVIF but (for various reasons) won't sync time via NTP correctly or lose their settings. It retrieves the hostname or IP of every camera to connect to from the ``Source`` (Path) field of each monitor in ZoneMinder.

## Usage

Configuration is via environment variables:

* ``ZM_API_URL`` - The URL to your ZoneMinder API, i.e. ``http://zmhost/zm/api/``
* ``ONVIF_USERNAME`` - The username to connect to ONVIF with
* ``ONVIF_PASSWORD`` - The password to connect to ONVIF with

### Python Script

Note that this script **requires** Python 3.12 or newer, for the `%:z` format option in `strftime`.

1. Clone this repo locally
2. Set up a virtualenv and install dependencies: ``python -mvenv venv && venv/bin/pip install -r requirements.txt``
3. ``ZM_API_URL=whatever ONVIF_USERNAME=admin ONVIF_PASSWORD=mypass venv/bin/python zm_onvif_datetime.py``

### Docker

First, export the environment variables listed above.

For help: ``docker run -it --rm -v /etc/localtime:/etc/localtime -e ZM_API_URL -e ONVIF_USERNAME -e ONVIF_PASSWORD jantman/zondeminder-onvif-date-time-setter:latest -h``

For a dry run, without making any changes: ``docker run -it --rm -v /etc/localtime:/etc/localtime -e ZM_API_URL -e ONVIF_USERNAME -e ONVIF_PASSWORD jantman/zondeminder-onvif-date-time-setter:latest -D``

To actually set the date and time: ``docker run -it --rm -v /etc/localtime:/etc/localtime -e ZM_API_URL -e ONVIF_USERNAME -e ONVIF_PASSWORD jantman/zondeminder-onvif-date-time-setter:latest``
