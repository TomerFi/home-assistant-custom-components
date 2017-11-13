import datetime
import logging
import json
import requests
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

GEONAMES = 'geonames'
HAVDALAH_MINUTES = 'havdalah_minutes_after_sundown'
CANDLE_LIGHT_MINUTES = 'candle_lighting_minutes_before_sunset'

HAVDALAH_DEFAULT = 36
CANDLE_LIGHT_DEFAULT = 18
SCAN_INTERVAL = datetime.timedelta(seconds=60)

SHABBAT_START = 'shabbat_start'
SHABBAT_END = 'shabbat_end'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(GEONAMES): cv.string,
    vol.Optional(HAVDALAH_MINUTES, default=HAVDALAH_DEFAULT): int,
    vol.Optional(CANDLE_LIGHT_MINUTES, default=CANDLE_LIGHT_DEFAULT): int,
    vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period
})

TRACKABLE_DOMAINS = ['sensor']


def setup_platform(hass, config, add_devices, discovery_info=None):
    havdalah = config.get(HAVDALAH_MINUTES)
    candle_light = config.get(CANDLE_LIGHT_MINUTES)
    cities = config.get(GEONAMES)
    cities_list = cities.split(",")

    for city in cities_list:
        add_devices([ShabbatTimes(hass, city, 'Shabbat Times ' + city.replace('-', '_'), havdalah, candle_light)])


class ShabbatTimes(Entity):

    def __init__(self, hass, city, name, havdalah, candle_light):
        self._hass = hass
        self._city = city
        self._name = name
        self._havdalah = havdalah
        self._candle_light = candle_light
        self._state = 'Awaiting Update'
        self._shabbat_start = None
        self._shabbat_end = None

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def device_state_attributes(self):
        return{
            SHABBAT_START: self._shabbat_start,
            SHABBAT_END: self._shabbat_end,
            HAVDALAH_MINUTES: self._havdalah,
            CANDLE_LIGHT_MINUTES: self._candle_light
        }

    @Throttle(SCAN_INTERVAL)
    def update(self):
        self._state = 'Working'
        self.shabbat_start = None
        self._shabbat_end = None
        today = datetime.date.today()
        if (today.weekday == 5):
            friday = today + datetime.timedelta(-1)
        else:
            friday = today + datetime.timedelta((4-today.weekday()) % 7)

        saturday = friday + datetime.timedelta(+1)

        year = str(friday.year)
        month = str(friday.month)

        hebcal_url = "http://www.hebcal.com/hebcal/?v=1&cfg=json&maj=off&min=off&mod=off&nx=off&year=" + year + "&month=" + month + "&ss=off&mf=off&c=on&geo=city&city=" + self._city + "&m=" + str(self._havdalah) + "&s=off&i=off&b=" + str(self._candle_light)
        hebcal_response = requests.get(hebcal_url)
        hebcal_json_input = hebcal_response.text
        hebcal_decoded = json.loads(hebcal_json_input)

        if 'error' in hebcal_decoded:
            self._state = hebcal_decoded['error']
            _LOGGER.error(hebcal_decoded['error'])
        else:
            for item in hebcal_decoded['items']:
                if (item['category'] == 'candles'):
                    ret_date = datetime.datetime.strptime(item['date'][0:-6].replace('T',' '), '%Y-%m-%d %H:%M:%S')
                    if (ret_date.date() == friday):
                        self._shabbat_start = ret_date
                elif (item['category'] == 'havdalah'):
                    ret_date = datetime.datetime.strptime(item['date'][0:-6].replace('T',' '), '%Y-%m-%d %H:%M:%S')
                    if (ret_date.date() == saturday):
                        self._shabbat_end = ret_date

            self._state = 'Updated'
