import asyncio
import logging

import binascii as ba
import time
import struct
import socket

import voluptuous as vol

from homeassistant.components.switch import (PLATFORM_SCHEMA, SwitchDevice)
from homeassistant.const import (CONF_SWITCHES, CONF_FRIENDLY_NAME)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)

LOCAL_IP_ADDR = 'local_ip_addr'
PHONE_ID = 'phone_id'
DEVICE_ID = 'device_id'
DEVICE_PASSWORD = 'device_password'

SWITCH_SCHEMA = vol.Schema({
    vol.Required(CONF_FRIENDLY_NAME): cv.string,
    vol.Required(LOCAL_IP_ADDR): cv.string,
    vol.Required(PHONE_ID): cv.string,
    vol.Required(DEVICE_ID): cv.string,
    vol.Required(DEVICE_PASSWORD): cv.string
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SWITCHES, default={}):
        vol.Schema({cv.slug: SWITCH_SCHEMA})
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    devices = config.get(CONF_SWITCHES)

    switches = []

    for object_id, config in devices.items():
        friendly_name = config.get(CONF_FRIENDLY_NAME)
        local_ip_addr = config.get(LOCAL_IP_ADDR)
        phone_id = config.get(PHONE_ID)
        device_id = config.get(DEVICE_ID)
        device_password = config.get(DEVICE_PASSWORD)

        switches.append(SwitcherHeater(friendly_name, local_ip_addr, phone_id, device_id, device_password))

    add_devices(switches)


class SwitcherHeater(SwitchDevice):
    pSession = "00000000"
    pKey = b"00000000000000000000000000000000"

    def __init__(self, friendly_name, local_ip_addr, phone_id, device_id, device_password):
        # self.entity_id = ENTITY_ID_FORMAT.format((friendly_name.replace('-', '').replace(' ', '_')).lower())
        self._friendly_name = friendly_name
        self._local_ip_addr = local_ip_addr
        self._phone_id = phone_id
        self._device_id = device_id
        self._device_password = device_password
        self._state = False

        _LOGGER.debug('new entity established')

    # CRC Calculation
    def crcSignFullPacketComKey(self, pData):
        try:
            crc = (ba.hexlify(struct.pack('>I', ba.crc_hqx(ba.unhexlify(pData), 0x1021)))).decode('utf-8')
            pData = pData + crc[6:8] + crc[4:6]
            crc = crc[6:8] + crc[4:6] + (ba.hexlify(self.pKey)).decode('utf-8')
            crc = (ba.hexlify(struct.pack('>I', ba.crc_hqx(ba.unhexlify(crc), 0x1021)))).decode('utf-8')
            pData = pData + crc[6:8] + crc[4:6]
            return pData
        except:
            _LOGGER.exception('failed to sign crc')
            return None

    # Send packets to device
    def sendToDevice(self, cmd):
        sock = None
        try:
            # generate timestamp
            ts = (ba.hexlify(struct.pack('<I', int(round(time.time()))))).decode('utf-8')

            # connect to socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self._local_ip_addr, 9957))
            _LOGGER.debug('connected to socket')

            # send login packet
            data = "fef052000232a100" + self.pSession + "340001000000000000000000" + ts + "00000000000000000000f0fe1c00" + self._phone_id + "0000" + self._device_password + "00000000000000000000000000000000000000000000000000000000"
            data = self.crcSignFullPacketComKey(data)
            if data is None:
                return False
            sock.send(ba.unhexlify(data))
            res = sock.recv(1024)
            pSession2 = (ba.hexlify(res)[16:24]).decode('utf-8')
            _LOGGER.debug('login packet sent')

            # send second packet
            data = "fef0300002320103" + pSession2 + "340001000000000000000000" + ts + "00000000000000000000f0fe" + self._device_id + "00"
            data = self.crcSignFullPacketComKey(data)
            if data is None:
                return False
            sock.send(ba.unhexlify(data))
            res = sock.recv(1024)
            _LOGGER.debug('second packet sent')

            # send control packet
            data = "fef05d0002320102" + pSession2 + "340001000000000000000000" + ts + "00000000000000000000f0fe" + self._device_id + "00" + self._phone_id + "0000" + self._device_password + "000000000000000000000000000000000000000000000000000000000106000" + cmd + "0000000000"
            data = self.crcSignFullPacketComKey(data)
            if data is None:
                return False
            sock.send(ba.unhexlify(data))
            res = sock.recv(1024)
            _LOGGER.debug('control packet sent')

            if cmd == "0":
                return False
            elif cmd == "1":
                return True
            else:
                return False

        except:
            _LOGGER.exception('failed to connect and send packet to device')
            return False

        finally:
            if not (sock is None):
                sock.close()
                _LOGGER.debug('socket connection closed')

    @property
    def name(self):
        return self._friendly_name

    @property
    def assumed_state(self):
        return True

    @property
    def should_poll(self):
        return False

    @property
    def is_on(self):
        return self._state

    def turn_on(self, **kwargs):
        _LOGGER.debug('received turn on request')
        self._state = self.sendToDevice("1")
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        _LOGGER.debug('received turn off request')
        self._state = self.sendToDevice("0")
        self.schedule_update_ha_state()
