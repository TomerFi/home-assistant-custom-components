import asyncio
import logging
import json
import datetime

import voluptuous as vol

from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.restore_state import async_get_last_state
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['notify']

DOMAIN = 'date_notifier'
ENTITY_ID_FORMAT = DOMAIN + '.{}'

NAME = 'name'
HOUR = 'hour'
MINUTE = 'minute'
MINUTE_DEFAULT = 0
DAY = 'day'
MONTH = 'month'
YEAR = 'year'
MESSAGE = 'message'
DAYS_NOTICE = 'days_notice'
DAYS_NOTICE_DEFAULT = 0
NOTIFIER = 'notifier'
COUNTDOWN = 'countdown'
COUNTDOWN_DEFAULT = False

RECURRENCE = 'recurrence'
INTERVAL = datetime.timedelta(minutes=1)
SERVICE_SCAN_DATES = "scan_dates"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        cv.slug: vol.All({
            vol.Required(NAME): cv.string,
            vol.Required(HOUR): cv.positive_int,
            vol.Required(MESSAGE): cv.string,
            vol.Required(NOTIFIER): cv.string,
            vol.Optional(DAYS_NOTICE, default=DAYS_NOTICE_DEFAULT): cv.positive_int,
            vol.Optional(DAY): cv.positive_int,
            vol.Optional(MINUTE, default=MINUTE_DEFAULT): cv.positive_int,
            vol.Optional(MONTH): cv.positive_int,
            vol.Optional(YEAR): cv.positive_int,
            vol.Optional(COUNTDOWN, default=COUNTDOWN_DEFAULT): cv.boolean
        })
    })
}, extra=vol.ALLOW_EXTRA)


@asyncio.coroutine
def async_setup(hass, config):
    component = EntityComponent(_LOGGER, DOMAIN, hass)

    entities = []

    for name, config in config[DOMAIN].items():
        if not config:
            config = {}

        name = config.get(NAME)
        hour = config.get(HOUR)
        minute = config.get(MINUTE)
        day = None
        month = None
        year = None
        message = config.get(MESSAGE)
        days_notice = config.get(DAYS_NOTICE)
        notifier = config.get(NOTIFIER).replace('notify.', '')
        countdown = config.get(COUNTDOWN)
        recurrence = 'daily'
        if config.get(DAY):
            day = config.get(DAY)
            recurrence = 'monthly'
        if config.get(MONTH):
            month = config.get(MONTH)
            recurrence = 'yearly'
        if config.get(YEAR):
            year = config.get(YEAR)
            calc_date = datetime.datetime.now().replace(second=0, microsecond=0)
            reminder_set = datetime.datetime.strptime(str(year) + '-' + str(month) + '-' + str(day) + ' ' + str(hour) + ':' + str(minute), '%Y-%m-%d %H:%M') + datetime.timedelta(-days_notice)
            if calc_date > reminder_set:
                recurrence = 'past_due'
            else:
                recurrence = 'on_date'

        entities.append(DateNotifier(name, hour, minute, day, month, year, message, days_notice, notifier, recurrence, countdown))

    @asyncio.coroutine
    def async_scan_dates_service(call):
        for entity_id in component.entities:
            entity = component.entities[entity_id]

            if entity:
                target_notifiers = [entity]
                tasks = [notifier.async_scan_dates() for notifier in target_notifiers]
                if tasks:
                    yield from asyncio.wait(tasks, loop=hass.loop)
                else:
                    _LOGGER.error('no tasks initialized for ' + entity_id)
            else:
                _LOGGER.error('no entity found with the name ' + entity_id)

    async_track_time_interval(hass, async_scan_dates_service, INTERVAL)

    yield from component.async_add_entities(entities)
    return True


class DateNotifier(Entity):

    def __init__(self, name, hour, minute, day, month, year, message, days_notice, notifier, recurrence, countdown):
        self.entity_id = ENTITY_ID_FORMAT.format(name.replace('-', '').replace(' ', '_'))
        self._name = name
        self._hour = hour
        self._minute = minute
        self._day = day
        self._month = month
        self._message = message
        self._days_notice = days_notice
        self._notifier = notifier
        self._year = year
        self._recurrence = recurrence
        self._countdown = countdown

    @asyncio.coroutine
    def async_added_to_hass(self):
        state = yield from async_get_last_state(self.hass, self.entity_id)
        if state:
            self._value = state.state

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return None

    @property
    def state(self):
        return self._recurrence

    @property
    def state_attributes(self):
        if self._recurrence == 'daily':
            return{
                NAME: self._name,
                HOUR: self._hour,
                MINUTE: self._minute,
                MESSAGE: self._message,
                NOTIFIER: self._notifier,
                RECURRENCE: self._recurrence,
                COUNTDOWN: self._countdown
            }
        elif self._recurrence == 'monthly':
            return{
                NAME: self._name,
                HOUR: self._hour,
                MINUTE: self._minute,
                DAY: self._day,
                MESSAGE: self._message,
                DAYS_NOTICE: self._days_notice,
                NOTIFIER: self._notifier,
                RECURRENCE: self._recurrence,
                COUNTDOWN: self._countdown
            }
        elif self._recurrence == 'yearly':
            return{
                NAME: self._name,
                HOUR: self._hour,
                MINUTE: self._minute,
                DAY: self._day,
                MONTH: self._month,
                MESSAGE: self._message,
                DAYS_NOTICE: self._days_notice,
                NOTIFIER: self._notifier,
                RECURRENCE: self._recurrence,
                COUNTDOWN: self._countdown
            }
        else:
            return{
                NAME: self._name,
                HOUR: self._hour,
                MINUTE: self._minute,
                DAY: self._day,
                MONTH: self._month,
                YEAR: self._year,
                MESSAGE: self._message,
                DAYS_NOTICE: self._days_notice,
                NOTIFIER: self._notifier,
                RECURRENCE: self._recurrence,
                COUNTDOWN: self._countdown
            }

    @callback
    def async_scan_dates(self):

        calc_date = datetime.datetime.now().replace(second=0, microsecond=0)

        if self._recurrence.lower() != 'past_due':
            days_notice = self._days_notice
            if self._recurrence == 'on_date':
                reminder_set = datetime.datetime.strptime(str(self._year) + '-' + str(self._month) + '-' + str(self._day) + ' ' + str(self._hour) + ':' + str(self._minute), '%Y-%m-%d %H:%M') + datetime.timedelta(-days_notice)
                if calc_date >= reminder_set:
                    self._recurrence = 'past_due'
            elif self._recurrence == 'yearly':
                reminder_set = datetime.datetime.strptime(str(calc_date.year) + '-' + str(self._month) + '-' + str(self._day) + ' ' + str(self._hour) + ':' + str(self._minute), '%Y-%m-%d %H:%M') + datetime.timedelta(-days_notice)
            elif self._recurrence == 'monthly':
                reminder_set = datetime.datetime.strptime(str(calc_date.year) + '-' + str(calc_date.month) + '-' + str(self._day) + ' ' + str(self._hour) + ':' + str(self._minute), '%Y-%m-%d %H:%M') + datetime.timedelta(-days_notice)
            elif self._recurrence == 'daily':
                days_notice = 0
                reminder_set = datetime.datetime.strptime(str(calc_date.year) + '-' + str(calc_date.month) + '-' + str(calc_date.day) + ' ' + str(self._hour) + ':' + str(self._minute), '%Y-%m-%d %H:%M')

            if calc_date == reminder_set:
                message = self._message
                if days_notice == 0:
                    message = message + ' is due today.'
                elif days_notice == 1:
                    message = message + ' is due tommorow.'
                else:
                    message = message + ' is due in ' + str(days_notice) + ' days.'
                service_data = {"title": "DateNotifier", "message": message}
                self.hass.async_add_job(self.hass.services.async_call('notify', self._notifier, service_data=service_data, blocking=False))
                yield from self.async_update_ha_state()
