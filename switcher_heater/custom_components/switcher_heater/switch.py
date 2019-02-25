"""////////////////////////////////////////////////////////////////////////////////////////////////
Home Assistant Custom Component for turning on/off the SwitcherV2 water heater.
Build by TomerFi
Please visit https://github.com/TomerFi/home-assistant-custom-components for more custom components

installation notes:
place this file in the following folder and restart home assistant:
/config/custom_components/switch

if error occures, raise the log level to debug mode and analyze the logs:
                    custom_components.switch.switcher_heater: debug

yaml configuration example:

switch:
  - platform: switcher_heater
    switches:
      device_id:
        friendly_name: 'heater_switch'
        local_ip_addr: 'XXX.XXX.XXX.XXX'
        phone_id: 'XXXX'
        device_id: 'XXXXXX'
        device_password: 'XXXXXXXX'
        scan_interval: 20
        icon: 'mdi:thermostat-box'

////////////////////////////////////////////////////////////////////////////////////////////////"""
import asyncio
import logging

import binascii as ba
import time
from struct import pack
import socket
import datetime
import traceback

import voluptuous as vol

from homeassistant.components.switch import (PLATFORM_SCHEMA, SwitchDevice, ENTITY_ID_FORMAT)
from homeassistant.const import (CONF_SWITCHES, CONF_FRIENDLY_NAME, CONF_SCAN_INTERVAL, CONF_IP_ADDRESS, STATE_ON, STATE_OFF, CONF_ENTITY_ID, CONF_ICON)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import (async_track_time_interval, async_track_state_change)
from homeassistant.core import callback
from homeassistant.helpers.entity import async_generate_entity_id

REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)

"""###############################
##### Home Assistant Naming ######
###############################"""
DOMAIN = "switch"
NOTIFY_DOMAIN = "notify"
PLATFORM = "switcher_heater_{}"
TURN_ON_15_SERVICE = PLATFORM.format("turn_on_15_minutes")
TURN_ON_30_SERVICE = PLATFORM.format("turn_on_30_minutes")
TURN_ON_45_SERVICE = PLATFORM.format("turn_on_45_minutes")
TURN_ON_60_SERVICE = PLATFORM.format("turn_on_60_minutes")
SET_AUTO_OFF_SERVICE = PLATFORM.format("set_auto_off")

"""###############################
#### Configuration Constants #####
###############################"""
CONF_LOCAL_IP_ADDR = 'local_ip_addr' # consider replacing CONF_LOCAL_IP_ADDR to const.CONF_IP_ADDRESS
CONF_PHONE_ID = 'phone_id'
CONF_DEVICE_ID = 'device_id'
CONF_DEVICE_PASSWORD = 'device_password'
CONF_NOTIFY_SERVICE_NAME = "notify_service_name"
CONF_AUTO_OFF_CONFIG = "auto_off"

"""###############################
######## Default Values ##########
###############################"""
DEFAULT_SCAN_INTERVAL = 20
DEFAULT_NAME = "SwitcherV2 Device"
DEFAULT_ICON = "mdi:thermostat-box"

"""###############################
##### Attributes Constants #######
###############################"""
ATTR_CURRENT_POWER_WATTS = "current_power_watts"
ATTR_CURRENT_POWER_AMPS = "current_power_amps"
ATTR_AUTO_OFF_TIME_LEFT = "auto_off_time_left"
ATTR_AUTO_OFF_CONFIG = "auto_off_configuration"

"""###############################
###### Notification Dicts ########
###############################"""
TIMER_TURN_ON_NOTIFICATION_DATA = {
    "title": "SwitcherV2 Turned On",
    "message": "Device {} has been turned on for {} minutes."
}

TIMER_TURN_OFF_NOTIFICATION_DATA = {
    "title": "SwitcherV2 Turned Off",
    "message": "Device {} has been turned off."
}

"""###############################
##### Configuration Schemas ######
###############################"""
SWITCH_SCHEMA = vol.Schema({
    vol.Optional(CONF_FRIENDLY_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_LOCAL_IP_ADDR): cv.string,
    vol.Required(CONF_PHONE_ID): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_DEVICE_PASSWORD): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    vol.Optional(CONF_ICON, default=DEFAULT_ICON): cv.icon
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SWITCHES, default={}):
        vol.Schema({cv.slug: SWITCH_SCHEMA})
})

TIMER_SERVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_ids,
    vol.Optional(CONF_NOTIFY_SERVICE_NAME): cv.service
})

SET_AUTO_OFF_SERVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_ids,
    vol.Required(CONF_AUTO_OFF_CONFIG): cv.time_period_str
})

"""###############################
###### SwitcherV2 Constants ######
###############################"""
REMOTE_SESSION_ID = "00000000"
REMOTE_KEY = b"00000000000000000000000000000000"
SOCKET_PORT = 9957
NO_TIMER_REQUESTED = "00000000"

"""###############################
######### Packet Formats #########
###############################"""
# remote session id, timestamp, phone id, device password
LOGIN_PACKET = "fef052000232a100{}340001000000000000000000{}00000000000000000000f0fe1c00{}0000{}00000000000000000000000000000000000000000000000000000000"
# local session id, timestamp, device id
GET_STATE_PACKET = "fef0300002320103{}340001000000000000000000{}00000000000000000000f0fe{}00"
# local session id, timestamp, device id, phone id, device password, command (1/0), timer
SEND_CONTROL_PACKET = "fef05d0002320102{}340001000000000000000000{}00000000000000000000f0fe{}00{}0000{}000000000000000000000000000000000000000000000000000000000106000{}00{}"
# local session id, timestamp, device id, phone id, device password, auto-off seconds
SET_AUTO_OFF_PACKET ="fef05b0002320102{}340001000000000000000000{}00000000000000000000f0fe{}00{}0000{}00000000000000000000000000000000000000000000000000000000040400{}"

"""###############################
#### Tools Parsers Converters ####
###############################"""
@callback
def crc_sign_full_packet_com_key(pData):
    """CRC calculation"""
    try:
        crc = (ba.hexlify(pack('>I', ba.crc_hqx(ba.unhexlify(pData), 0x1021)))).decode('utf-8')
        pData = pData + crc[6:8] + crc[4:6]
        crc = crc[6:8] + crc[4:6] + (ba.hexlify(REMOTE_KEY)).decode('utf-8')
        crc = (ba.hexlify(pack('>I', ba.crc_hqx(ba.unhexlify(crc), 0x1021)))).decode('utf-8')
        pData = pData + crc[6:8] + crc[4:6]
        return pData
    except:
        _LOGGER.exception('failed to sign crc ' + traceback.format_exc())
        return None

@callback
def get_timestamp():
    """Generate timestamp"""
    return (ba.hexlify(pack('<I', int(round(time.time()))))).decode('utf-8')

@callback
def get_socket(ip_addr):
    """Connect to socket"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip_addr, SOCKET_PORT))
        _LOGGER.debug('connected socket to ' + ip_addr)
        return sock
    except:
        _LOGGER.error('failed to connect socket to ' + ip_addr + traceback.format_exc())
        return None

@callback
def close_socket_connection(sock, ip_addr):
    """Close socket"""
    try:
        if not sock is None:
            sock.close()
            _LOGGER.debug('closed socket connection to ' + ip_addr)
    except:
        pass

@callback
def convert_minutes_to_timer(minutes):
    """convert minutes to hex for timer"""
    return (ba.hexlify(pack('<I', int(minutes) * 60 ))).decode('utf-8')

@callback
def convert_seconds_to_iso_time(all_seconds):
    """convert seconds to iso time (%H:%M:%S)"""
    minutes, seconds = divmod(int(all_seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return datetime.time(hour=hours, minute=minutes, second=seconds).isoformat(timespec='auto')

@callback
def convert_timedelta_to_auto_off(full_time):
    """convert timedelta seconds to hex for auto-off"""
    auto_off = auto_off_config = None
    try:
        minutes = full_time.total_seconds() / 60
        hours, minutes = divmod(minutes, 60)
        seconds = int(hours) * 3600 + int(minutes) * 60
        if seconds > 3599 and seconds < 86341:
            auto_off = (ba.hexlify(pack('<I', int(seconds)))).decode('utf-8')
            auto_off_config = convert_seconds_to_iso_time(seconds)
    except:
        _LOGGER.warning('failed to create auto-off from timedelta')

    return auto_off, auto_off_config

@callback
def parse_power_consumption(response):
    """parse power consumption"""
    current_power_w = current_power_a = None
    try:
        power = ba.hexlify(response)[154:162]
        current_power_w = int(power[2:4] + power[0:2], 16)
        current_power_a = round((current_power_w / float(220)), 1)
    except:
        _LOGGER.warning('failed to parse power consumption data from response')

    return current_power_w, current_power_a

@callback
def parse_auto_off_time_left(response):
    """parse time left to auto off"""
    auto_off_time_left = None
    try:
        time_left = ba.hexlify(response)[178:186]
        all_seconds = int(time_left[6:8] + time_left[4:6] + time_left[2:4] + time_left[0:2] , 16)
        auto_off_time_left = convert_seconds_to_iso_time(all_seconds)
    except:
        _LOGGER.warning('failed to parse off timer data from response')

    return auto_off_time_left

@callback
def parse_auto_off_config(response):
    """parse time left to auto off"""
    auto_off_config = None
    try:
        time_left = ba.hexlify(response)[194:202]
        all_seconds = int(time_left[6:8] + time_left[4:6] + time_left[2:4] + time_left[0:2] , 16)
        auto_off_config = convert_seconds_to_iso_time(all_seconds)
    except:
        _LOGGER.warning('failed to parse off timer data from response')

    return auto_off_config

@callback
def parse_status(response):
    """parse time left to auto off"""
    current_status = None
    try:
        state = (ba.hexlify(response)[150:154]).decode('utf-8')
        if state == "0000":
            current_status = STATE_OFF
        elif state == "0100":
            current_status = STATE_ON

    except:
        _LOGGER.warning('failed to parse current status data from response')

    return current_status

"""############################
####### Packet Handlers #######
############################"""
@asyncio.coroutine
def async_send_login_packet(phone_id, device_password, sock, ts, retry=3):
    """Send login packet"""
    session_id = None
    try:
        packet = crc_sign_full_packet_com_key(LOGIN_PACKET.format(REMOTE_SESSION_ID, ts, phone_id, device_password))
        if not packet is None:
            sock.send(ba.unhexlify(packet))
            res = sock.recv(1024)
            session_id = (ba.hexlify(res)[16:24]).decode('utf-8')
            _LOGGER.debug('login packet sent, retreived session id is: ' + session_id)
            if (session_id is None or session_id == ""):
                if (retry > 0):
                    _LOGGER.warning('failed to get session id from device, retrying')
                    return async_send_login_packet(phone_id, device_password, sock, ts, retry - 1)
                else:
                    _LOGGER.error('failed to session id from device, please try again later')
                    session_id = None
    except:
        _LOGGER.error('failed to send login packet ' + traceback.format_exc())

    return session_id

@asyncio.coroutine
def async_send_get_state_packet(device_id, sock, ts, session_id):
    """Send get state packet"""
    current_status = current_power_w = current_power_a = auto_off_time_left = auto_off_config = None
    try:
        packet = crc_sign_full_packet_com_key(GET_STATE_PACKET.format(session_id, ts, device_id))
        if not packet is None:
            sock.send(ba.unhexlify(packet))
            res = sock.recv(1024)
            current_status = parse_status(res)
            if not current_status is None:
                auto_off_config = parse_auto_off_config(res)
                _LOGGER.debug('state packet sent, device current state is ' + current_status)
                if current_status == STATE_ON:
                    current_power_w, current_power_a = parse_power_consumption(res)
                    auto_off_time_left = parse_auto_off_time_left(res)
            else:
               _LOGGER.debug('state packet sent, failed to extract status from response') 
    except:
        _LOGGER.error('failed to send get state packet ' + traceback.format_exc())

    return current_status, current_power_w, current_power_a, auto_off_time_left, auto_off_config

@asyncio.coroutine
def async_send_control_packet(device_id, phone_id, device_password, sock, ts, session_id, cmd, timer=None):
    """Send control packet"""
    status = power_w = power_a = auto_off_time_left = None
    try:
        if timer is None:
            """No timer requested"""
            packet = crc_sign_full_packet_com_key(SEND_CONTROL_PACKET.format(session_id, ts, device_id, phone_id, device_password, cmd, NO_TIMER_REQUESTED))
        else:
            """Incorporate timer in packet"""
            _LOGGER.debug('incorporating timer for ' + timer + ' minutes')
            packet = crc_sign_full_packet_com_key(SEND_CONTROL_PACKET.format(session_id, ts, device_id, phone_id, device_password, cmd, convert_minutes_to_timer(timer)))
        
        if not packet is None:
            sock.send(ba.unhexlify(packet))
            res = sock.recv(1024)
            if cmd == "0":
                _LOGGER.debug('control packet sent for state off')
                status = STATE_OFF
            elif cmd == "1":
                _LOGGER.debug('control packet sent for state on')
                power_w = power_a = 0
                if not timer is None:
                    auto_off_time_left = convert_seconds_to_iso_time(str(int(timer) * 60))
                    
                status = STATE_ON
    except:
        _LOGGER.error('failed to send control packet ' + traceback.format_exc())

    return status, power_w, power_a, auto_off_time_left

@asyncio.coroutine
def async_send_set_auto_off_packet(device_id, phone_id, device_password, full_time, sock, ts, session_id):
    """Send set auto-off packet"""
    auto_off_config = None
    try:
        prep_auto_off, auto_off_config = convert_timedelta_to_auto_off(full_time)
        if not prep_auto_off is None:
            packet = crc_sign_full_packet_com_key(SET_AUTO_OFF_PACKET.format(session_id, ts, device_id, phone_id, device_password, prep_auto_off))
            if not packet is None:
                sock.send(ba.unhexlify(packet))
                res = sock.recv(1024)
        else:
            _LOGGER.error('failed to validate input. the correct format is HH:mm with a minimum of 01:00 and maximum of 23:59')
    except:
        _LOGGER.error('failed to send set auto-off packet ' + traceback.format_exc())

    return auto_off_config

"""###########################
###### Platform Setup ########
###########################"""
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Initialize the platform"""
    devices = config.get(CONF_SWITCHES)

    switches = []

    for object_id, config in devices.items():
        generated_entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, object_id, hass=hass)
        name = config.get(CONF_FRIENDLY_NAME)
        ip_address = config.get(CONF_LOCAL_IP_ADDR)
        phone_id = config.get(CONF_PHONE_ID)
        device_id = config.get(CONF_DEVICE_ID)
        device_password = config.get(CONF_DEVICE_PASSWORD)
        scan_interval = config.get(CONF_SCAN_INTERVAL) if config.get(CONF_SCAN_INTERVAL) >= DEFAULT_SCAN_INTERVAL else DEFAULT_SCAN_INTERVAL
        icon = config.get(CONF_ICON)
        
        device = SwitcherHeater(generated_entity_id, name, ip_address, phone_id, device_id, device_password, scan_interval, icon)

        async_track_time_interval(hass, device.async_update_device_state, datetime.timedelta(seconds=scan_interval))
        switches.append(device)

    @asyncio.coroutine
    def async_turn_on_with_timer_service(service):
        """Service for handling turn on with 15/30/45/60 minutes timer"""
        notify_service = None
        if CONF_NOTIFY_SERVICE_NAME in service.data:
            """Include notification message services"""
            service_name = service.data[CONF_NOTIFY_SERVICE_NAME]
            service_name_clean = service_name.replace(NOTIFY_DOMAIN + ".", "")
            if (hass.services.has_service(NOTIFY_DOMAIN, service_name_clean)):
                _LOGGER.debug("notification service found: " + NOTIFY_DOMAIN + "." + service_name_clean)
                notify_service = (service_name_clean)
            else:
                _LOGGER.error(service_name + " is not a legitimate notify service name")

        for entity_id in service.data[CONF_ENTITY_ID]:
            if service.service == TURN_ON_15_SERVICE:
                minutes = "15"
            elif service.service == TURN_ON_30_SERVICE:
                minutes = "30"
            elif service.service == TURN_ON_45_SERVICE:
                minutes = "45"
            elif service.service == TURN_ON_60_SERVICE:
                minutes = "60"

            _LOGGER.debug("received turn on with " + minutes + " minutes timer request id " + service.call_id + " for " + entity_id)

            for switch in switches:
                found = False
                if switch.entity_id == entity_id:
                    found = True
                    yield from hass.async_add_job(switch.async_turn_on_with_timer(minutes, notify_service))
                    break
                if not found:
                    _LOGGER.error("the entity id " + entity_id + " is not a switcher device")

    @asyncio.coroutine
    def async_set_auto_off_service(service):
        for entity_id in service.data[CONF_ENTITY_ID]:
            for switch in switches:
                found = False
                if switch.entity_id == entity_id:
                    found = True
                    yield from hass.async_add_job(switch.async_set_auto_off(service.data[CONF_AUTO_OFF_CONFIG]))
                    break
                if not found:
                    _LOGGER.error("the entity id " + entity_id + " is not a switcher device")

    if switches:
        hass.services.async_register(DOMAIN, TURN_ON_15_SERVICE, async_turn_on_with_timer_service, schema=TIMER_SERVICE_SCHEMA)
        hass.services.async_register(DOMAIN, TURN_ON_30_SERVICE, async_turn_on_with_timer_service, schema=TIMER_SERVICE_SCHEMA)
        hass.services.async_register(DOMAIN, TURN_ON_45_SERVICE, async_turn_on_with_timer_service, schema=TIMER_SERVICE_SCHEMA)
        hass.services.async_register(DOMAIN, TURN_ON_60_SERVICE, async_turn_on_with_timer_service, schema=TIMER_SERVICE_SCHEMA)
        hass.services.async_register(DOMAIN, SET_AUTO_OFF_SERVICE, async_set_auto_off_service, schema=SET_AUTO_OFF_SERVICE_SCHEMA)
        
        async_add_devices(switches, True)

    return True

"""###########################
##### SwitcherV2 Entity ######
###########################"""
class SwitcherHeater(SwitchDevice):
    def __init__(self, generated_entity_id, name, ip_address, phone_id, device_id, device_password, scan_interval, icon):
        """Initialize the device"""
        self.entity_id = generated_entity_id
        self._name = name
        self._ip_address = ip_address
        self._phone_id = phone_id
        self._device_id = device_id
        self._device_password = device_password
        self._scan_interval = scan_interval
        self._icon = icon

        self._state = None
        self._skip_update = False
        self._current_power_w = None
        self._current_power_a = None
        self._listenr_remove_func = None
        self._auto_off_time_left = None
        self._auto_off_config = None

        _LOGGER.debug('new entity established: ' + self.entity_id)

    """############################
    ###### Request Handlers #######
    ############################"""
    @asyncio.coroutine
    def async_send_command_to_device(self, cmd, timer=None):
        """Handles control requests"""
        status = current_power_w = current_power_a = auto_off_time_left = auto_off_config = None
        try:
            sock = get_socket(self._ip_address)
            if not sock is None:
                ts = get_timestamp()
                session_id = yield from async_send_login_packet(self._phone_id, self._device_password, sock, ts)
                if not session_id is None:
                    status, current_power_w, current_power_a, auto_off_time_left, auto_off_config =  yield from async_send_get_state_packet(self._device_id, sock, ts, session_id)
                    if not status is None:
                        status, current_power_w, current_power_a, auto_off_time_left = yield from async_send_control_packet(self._device_id, self._phone_id, self._device_password, sock, ts, session_id, cmd, timer)
                    close_socket_connection(sock, self._ip_address)
        except:
            _LOGGER.error('failed to set the state of the device ' + traceback.format_exc())

        return status, current_power_w, current_power_a, auto_off_time_left, auto_off_config

    @asyncio.coroutine
    def async_get_state_of_device(self):
        """Handles update requests"""
        status = current_power_w = current_power_a = auto_off_time_left = auto_off_config = None
        try:
            sock = get_socket(self._ip_address)
            if not sock is None:
                ts = get_timestamp()
                session_id = yield from async_send_login_packet(self._phone_id, self._device_password, sock, ts)
                if not session_id is None:
                    status, current_power_w, current_power_a, auto_off_time_left, auto_off_config = yield from async_send_get_state_packet(self._device_id, sock, ts, session_id)
                    close_socket_connection(sock, self._ip_address)
        except:
            _LOGGER.error('failed to update device ' + traceback.format_exc())

        return status, current_power_w, current_power_a, auto_off_time_left, auto_off_config

    @asyncio.coroutine
    def async_set_auto_off_to_device(self, full_time):
        """Handles control requests"""
        status = current_power_w = current_power_a = auto_off_time_left = auto_off_config = None
        try:
            sock = get_socket(self._ip_address)
            if not sock is None:
                ts = get_timestamp()
                session_id = yield from async_send_login_packet(self._phone_id, self._device_password, sock, ts)
                if not session_id is None:
                    status, current_power_w, current_power_a, auto_off_time_left, auto_off_config =  yield from async_send_get_state_packet(self._device_id, sock, ts, session_id)
                    if not status is None:
                        auto_off_config = yield from async_send_set_auto_off_packet(self._device_id, self._phone_id, self._device_password, full_time, sock, ts, session_id)
                    close_socket_connection(sock, self._ip_address)
        except:
            _LOGGER.error('failed to set auto-off for the device ' + traceback.format_exc())

        return status, current_power_w, current_power_a, auto_off_time_left, auto_off_config

    """############################
    ###### Entity Properties ######
    ############################"""
    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def assumed_state(self):
        """Return true if unable to access real state of entity."""
        return False

    @property
    def should_poll(self):
        """Return true if the device should be polled for state updates"""
        return False

    @property
    def available(self):
        """Return true if the device is available for use."""
        return self._state is not None

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state == STATE_ON

    @property
    def icon(self):
        """Return the icon to display."""
        return self._icon

    @property
    def current_power_w(self):
        """Return the current power usage in W."""
        return self._current_power_w

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        attributes = {
            CONF_SCAN_INTERVAL: self._scan_interval,
            CONF_IP_ADDRESS: self._ip_address
        }

        if not self._current_power_w is None:
            attributes[ATTR_CURRENT_POWER_WATTS] = self._current_power_w
        if not self._current_power_a is None:
            attributes[ATTR_CURRENT_POWER_AMPS] = self._current_power_a
        if not self._auto_off_time_left is None:
            attributes[ATTR_AUTO_OFF_TIME_LEFT] = self._auto_off_time_left
        if not self._auto_off_config is None:
            attributes[ATTR_AUTO_OFF_CONFIG] = self._auto_off_config

        return attributes

    """############################
    ####### Entity Services #######
    ############################"""
    @asyncio.coroutine
    def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        _LOGGER.debug('received turn on request')
        """Skips next update after state changed, usefull for slow devices. if intial interval value was bigger or equals to 30, skip request will be ignored"""
        self._skip_update = True
        self._state, self._current_power_w, self._current_power_a, self._auto_off_time_left, self._auto_off_config = yield from self.hass.async_add_job(self.async_send_command_to_device,  "1")
        if self._state is None:
            self._skip_update = False
        if self._auto_off_time_left is None:
            self._auto_off_time_left = self._auto_off_config
        yield from self.async_update_ha_state()

    @asyncio.coroutine
    def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        _LOGGER.debug('received turn off request')
        """Skips next update after state changed, usefull for slow devices. if intial interval value was bigger or equals to 30, skip request will be ignored"""
        self._skip_update = True
        self._state, self._current_power_w, self._current_power_a, self._auto_off_time_left, self._auto_off_config = yield from self.hass.async_add_job(self.async_send_command_to_device,  "0")
        if self._state is None:
            self._skip_update = False
        yield from self.async_update_ha_state()

    @asyncio.coroutine
    def async_turn_on_with_timer(self, minutes, notify_service):
        """Turn the switch on with 15/30/45/60 minutes timer."""
        _LOGGER.debug('received turn on request')
        """Skips next update after state changed, usefull for slow devices. if intial interval value was bigger or equals to 30, skip request will be ignored"""
        self._skip_update = True
        self._state, self._current_power_w, self._current_power_a, self._auto_off_time_left, self._auto_off_config = yield from self.hass.async_add_job(self.async_send_command_to_device,  "1", minutes)
        if self._state is None:
            self._skip_update = False
        elif not notify_service is None:
            """Handle notification services turned on request"""
            ON_DATA = TIMER_TURN_ON_NOTIFICATION_DATA
            ON_DATA["message"] = ON_DATA["message"].format(self._name, minutes)
            self.hass.async_add_job(self.hass.services.async_call(NOTIFY_DOMAIN, notify_service, ON_DATA))
            _LOGGER.debug('turned on notification sent to ' + notify_service)

            """Handle notification services turned off registration"""
            OFF_DATA = TIMER_TURN_OFF_NOTIFICATION_DATA
            OFF_DATA["message"] = OFF_DATA["message"].format(self._name)
            
            @callback
            def send_turn_off_notification(entity, from_state, to_state):
                """Callback function for handling state changes"""
                _LOGGER.debug("received track event: " + str(entity) + " has changed state from " + str(from_state) + " to " + str(to_state))
                self.hass.async_add_job(self.hass.services.async_call(NOTIFY_DOMAIN, notify_service, OFF_DATA))
                _LOGGER.debug('turned off notification sent to ' + notify_service)
                if not self._listenr_remove_func is None:
                    """Remove listener for recieving anymore state changes tracking"""
                    self._listenr_remove_func()
                    self._listenr_remove_func = None
                    _LOGGER.debug('state change listener removed')

            """Register callback function for state change tracking"""
            if not self._listenr_remove_func is None:
                self._listenr_remove_func()
            self._listenr_remove_func = async_track_state_change(self.hass, self.entity_id, send_turn_off_notification, to_state=STATE_OFF)
            _LOGGER.debug('turned off notification registered to ' + notify_service)

        yield from self.async_update_ha_state()

    @asyncio.coroutine
    def async_set_auto_off(self, full_time):
        """Turn the switch off."""
        _LOGGER.debug('received turn off request')
        """Skips next update after state changed, usefull for slow devices. if intial interval value was bigger or equals to 30, skip request will be ignored"""
        self._skip_update = True
        self._state, self._current_power_w, self._current_power_a, self._auto_off_time_left, self._auto_off_config = yield from self.hass.async_add_job(self.async_set_auto_off_to_device , full_time)
        if self._state is None:
            self._skip_update = False
        yield from self.async_update_ha_state()

    @asyncio.coroutine
    def async_update_device_state(self, event):
        """Update the device's state and attributes"""
        _LOGGER.debug('received update request')
        if self._skip_update == True and self._scan_interval < 30:
            _LOGGER.debug('skipping unnecessary update request')
        else:
            self._state, self._current_power_w, self._current_power_a, self._auto_off_time_left, self._auto_off_config = yield from self.hass.async_add_job(self.async_get_state_of_device)
            
        self._skip_update = False
        yield from self.async_update_ha_state()
