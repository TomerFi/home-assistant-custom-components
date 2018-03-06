"""////////////////////////////////////////////////////////////////////////////////////////////////
Home Assistant Custom Component for Broadlink S1C Alarm kit integration as a Sensor platform.
Build by TomerFi
Please visit https://github.com/TomerFi/home-assistant-custom-components for more custom components

Tested in HassIO 0.63.3 for Door Sensors, Motion Sensors and Key Fobs

if error occures, raise the log level to debug mode and analyze the logs:
                    custom_components.sensor.broadlink_s1c: debug

installation notes:
place this file in the following folder and restart home assistant:
/config/custom_components/sensor

yaml configuration example:
sensor:
  - platform: broadlink_s1c
    ip_address: "xxx.xxx.xxx.xxx" # set your s1c hub local ip address
    mac: "XX:XX:XX:XX:XX:XX" # set your s1c hub mac address

////////////////////////////////////////////////////////////////////////////////////////////////"""
import binascii
import socket
import datetime
import logging
import asyncio
import traceback
import json
import threading
import broadlink

import voluptuous as vol

from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_IP_ADDRESS, CONF_MAC, CONF_TIMEOUT, STATE_UNKNOWN, STATE_OPEN, STATE_CLOSED,
    EVENT_HOMEASSISTANT_STOP, STATE_ALARM_DISARMED, STATE_ALARM_ARMED_HOME, STATE_ALARM_ARMED_AWAY)
from homeassistant.util.dt import now

"""current broadlink moudle in ha is of version 0.5 which doesn't supports s1c hubs, usuing version 0.6 from github"""
REQUIREMENTS = [
    'https://github.com/mjg59/python-broadlink/archive/master.zip'
    'master.zip#broadlink==0.6']

_LOGGER = logging.getLogger(__name__)

"""platform specifics"""
DOMAIN = 'sensor'
ENTITY_ID_FORMAT = DOMAIN + '.broadlink_s1c_{}'
DEFAULT_TIMEOUT = 10

"""additional states that doesn't exists in homeassistant.const"""
STATE_NO_MOTION = "no_motion"
STATE_MOTION_DETECTED = "motion_detected"
STATE_TAMPERED = "tampered"
STATE_ALARM_SOS = "sos"

"""sensor update event details"""
UPDATE_EVENT = "BROADLINK_S1C_SENSOR_UPDATE"
EVENT_PROPERTY_NAME = "name"
EVENT_PROPERTY_STATE = "state"

"""sensor types and icons"""
SENSOR_TYPE_DOOR_SENSOR = "Door Sensor"
SENSOR_TYPE_DOOR_SENSOR_ICON = "mdi:door"
SENSOR_TYPE_MOTION_SENSOR = "Motion Sensor"
SENSOR_TYPE_MOTION_SENSOR_ICON = "mdi:walk"
SENSOR_TYPE_KEY_FOB = "Key Fob"
SENSOR_TYPE_KEY_FOB_ICON = "mdi:remote"
SENSOR_DEFAULT_ICON = "mdi:security-home"

"""platform configuration schema"""
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int
})

"""set up broadlink s1c platform"""
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    _LOGGER.debug("starting platform setup")

    """get configuration params"""
    ip_address = config.get(CONF_IP_ADDRESS)
    mac = config.get(CONF_MAC).encode().replace(b':', b'')
    mac_addr = binascii.unhexlify(mac)
    timeout = config.get(CONF_TIMEOUT)

    """initiate connection to s1c hub"""
    conn_obj = HubConnection(ip_address, mac_addr, timeout)

    """discovering the sensors and initiating entities"""
    raw_data = conn_obj.get_initial_data()
    sensors = []
    for i, sensor in enumerate(raw_data["sensors"]):
        sensors.append(S1C_SENSOR(hass, sensor["name"], sensor["type"], conn_obj.parse_status(sensor["type"], str(sensor["status"])), now()))
    if sensors:
        async_add_devices(sensors, True)

    """starting the sensors status change watcher"""
    WatchSensors(hass, conn_obj).start()

    return True


class S1C_SENSOR(Entity):
    """representation of the sensor entity"""
    def __init__(self, hass, name, sensor_type, status, last_changed):
        """initialize the sensor entity"""
        self.entity_id = ENTITY_ID_FORMAT.format(name.replace(' ', '_').replace('-', '_').lower())
        self._hass = hass
        self._name = name
        self._sensor_type = sensor_type
        self._state = status
        self._last_changed = last_changed
        """registering entity for event listenting"""
        hass.bus.async_listen(UPDATE_EVENT, self.async_event_listener)
        _LOGGER.debug(self._name + " initiated")

    @property
    def name(self):
        """friendly name"""
        return self._name

    @property
    def should_poll(self):
        """entity should be polled for updates"""
        return False

    @property
    def state(self):
        """sensor state"""
        return self._state

    @property
    def icon(self):
        """sensor icon"""
        if (self._sensor_type == SENSOR_TYPE_DOOR_SENSOR):
            return SENSOR_TYPE_DOOR_SENSOR_ICON
        elif (self._sensor_type == SENSOR_TYPE_KEY_FOB):
            return SENSOR_TYPE_KEY_FOB_ICON
        elif (self._sensor_type == SENSOR_TYPE_KEY_FOB):
            return SENSOR_TYPE_KEY_FOB_ICON
        else:
            return SENSOR_DEFAULT_ICON


    @property
    def device_state_attributes(self):
        """sensor state attributes"""
        return {
            "sensor_type": self._sensor_type,
            "last_changed": self._last_changed
        }

    @asyncio.coroutine
    def async_event_listener(self, event):
        """handling incoming events and update ha state"""
        if (event.data.get(EVENT_PROPERTY_NAME) == self._name):
            _LOGGER.debug(self._name + " received " + UPDATE_EVENT)
            self._state = event.data.get(EVENT_PROPERTY_STATE)
            self._last_changed = event.time_fired
            yield from self.async_update_ha_state()


class HubConnection(object):
    """s1c hub connection and utility class"""
    def __init__(self, ip_addr, mac_addr, timeout):
        """initialize the connection object"""
        self._hub = broadlink.S1C((ip_addr, 80), mac_addr)
        self._hub.timeout = timeout
        self._authorized = self.authorize()
        if (self._authorized):
            _LOGGER.info("succesfully connected to s1c hub")
            self._initial_data = self._hub.get_sensors_status()
        else:
            _LOGGER.error("failed to connect s1c hub, not authorized. please fix the problem and restart the system")
            self._initial_data = None

    def authorize(self, retry=3):
        """authorize connection to s1c hub"""
        try:
            auth = self._hub.auth()
        except socket.timeout:
            auth = False
        if not auth and retry > 0:
            return self.authorize(retry-1)
        return auth

    def get_initial_data(self):
        """return initial data for discovery"""
        return self._initial_data

    def get_hub_connection(self):
        """return the connection object"""
        return self._hub

    def parse_status(self, sensor_type, sensor_status):
        """parse sensors status"""
        if sensor_type == SENSOR_TYPE_DOOR_SENSOR and sensor_status in ("0", "128"):
            return STATE_CLOSED
        elif sensor_type == SENSOR_TYPE_DOOR_SENSOR and sensor_status in ("16", "144"):
            return STATE_OPEN
        elif sensor_type == SENSOR_TYPE_DOOR_SENSOR and sensor_status == "48":
            return STATE_TAMPERED
        elif sensor_type == SENSOR_TYPE_MOTION_SENSOR and sensor_status in ("0", "128"):
            return STATE_NO_MOTION
        elif sensor_type == SENSOR_TYPE_MOTION_SENSOR and sensor_status == "16":
            return STATE_MOTION_DETECTED
        elif sensor_type == SENSOR_TYPE_MOTION_SENSOR and sensor_status == "32":
            return STATE_TAMPERED
        elif sensor_type == SENSOR_TYPE_KEY_FOB and sensor_status == "16":
            return STATE_ALARM_DISARMED
        elif sensor_type == SENSOR_TYPE_KEY_FOB and sensor_status == "32":
            return STATE_ALARM_ARMED_AWAY
        elif sensor_type == SENSOR_TYPE_KEY_FOB and sensor_status == "64":
            return STATE_ALARM_ARMED_HOME
        elif sensor_type == SENSOR_TYPE_KEY_FOB and sensor_status in ("0", "128"):
            return STATE_ALARM_SOS
        else:
            _LOGGER.debug("unknow status " + sensor_status + "for type " + sensor_type)
            return STATE_UNKNOWN


class WatchSensors(threading.Thread):
    """sensor status change watcher class"""
    def __init__(self, hass, conn_obj):
        
        threading.Thread.__init__(self)
        
        """initialize the watcher"""
        self._hass = hass
        self._ok_to_run = False
        self._conn_obj = conn_obj
        self._last_exception_dt = None
        self._exception_count = 0
        if (self._conn_obj._authorized):
            self._ok_to_run = True
            self._hub = self._conn_obj.get_hub_connection()

    def run(self):
        """register stop function for event listening"""
        self._hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, self.stop)
        
        """get initial sensors data"""
        if not (self._conn_obj.get_initial_data() is None):
            old_status = self._conn_obj.get_initial_data()
        else:
            old_status = self._hub.get_sensors_status()
        
        """start watcher loop"""
        _LOGGER.info("starting sensors watch")
        while self._ok_to_run:
            try:
                current_status = self._hub.get_sensors_status()
                for i, sensor in enumerate(current_status["sensors"]):
                    current_fixed_status = self._conn_obj.parse_status(sensor["type"], str(sensor["status"]))
                    previous_fixed_status = self._conn_obj.parse_status(old_status["sensors"][i]["type"], str(old_status["sensors"][i]["status"]))
                    if not (current_fixed_status == previous_fixed_status):
                        _LOGGER.debug("status change tracked from: " + json.dumps(old_status["sensors"][i]))
                        _LOGGER.debug("status change tracked to: " + json.dumps(sensor))
                        self.launch_state_change_event(sensor["name"], current_fixed_status)
                        old_status = current_status
            except:
                _LOGGER.error("exception while getting sensors status: " + traceback.format_exc())
                self.check_loop_run()
                continue
        _LOGGER.info("sensors watch done")

    def check_loop_run(self):
        """max exceptions allowed in loop before exiting"""
        max_exceptions_before_stop = 10
        """max minutes to remmember the last excption"""
        max_minutes_from_last_exception = 20
        
        current_dt = now()
        if not (self._last_exception_dt is None):
            if (self._last_exception_dt.year == current_dt.year and self._last_exception_dt.month == current_dt.month and self._last_exception_dt.day == current_dt.day):
                calc_dt = current_dt - self._last_exception_dt
                diff = divmod(calc_dt.days * 86400 + calc_dt.seconds, 60)
                if (diff[0] > max_minutes_from_last_exception):
                    self._exception_count = 0
                else:
                    self._exception_count += 1
            else:
                self._exception_count = 0
        else:
            self._exception_count = 0

        if not (max_exceptions_before_stop > self._exception_count):
            _LOGGER.error("max exceptions allowed in watch loop exceeded, stoping watch loop")
            self._ok_to_run = False

        self._last_exception_dt = current_dt

    def stop(self, event):
        """handle stop request for events"""
        _LOGGER.debug("received :" + event.event_type)
        self._ok_to_run = False

    def launch_state_change_event(self, name, status):
        """launch events for state changes"""
        _LOGGER.debug("launching event for " + name + "for state changed to " + status)
        self._hass.bus.fire(UPDATE_EVENT,
            {
                EVENT_PROPERTY_NAME: name,
                EVENT_PROPERTY_STATE: status
            })
