"""Support for plcbus switches."""
import logging
from typing import Optional


import voluptuous as vol

from .lib.plcbus_lib import PLCBUSAPI, PLCBUSException, get_plcbus_interface


import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.helpers.entity import ToggleEntity

_LOGGER = logging.getLogger(__name__)

DOMAIN = "plcbus"

ENTITY_ID_FORMAT = DOMAIN + ".{}"

CONF_USER_CODE = 'user_code'
CONF_DEVICE = 'device'
CONF_UNIT = 'unit'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USER_CODE): cv.string,
    vol.Optional(CONF_DEVICE, default=get_plcbus_interface()): cv.string,
    vol.Optional(CONF_UNIT, default=[]): vol.All(cv.ensure_list_csv, [cv.string]),
})
PlcbusSwitchList = []
device_found = []

def commandCB(self):
    _LOGGER.debug("commandCB")
    if self['d_command']=="GET_ALL_ID_PULSE":
        _LOGGER.debug ("get all id pulse reponse  %s",self)
        _LOGGER.debug ("data1=%s",self['d_data1'])
        _LOGGER.debug ("data2=%s",self['d_data2'])
        for i in range(0, 8):
            if self['d_data2'] >> i & 1:
                _LOGGER.info ("Find a device with unit_code %s", self['d_home_unit'][0] + str(i+1))
                device_found.append(self['d_home_unit'][0] + str(i+1))
        for i in range(0, 8):
            if self['d_data1'] >> i & 1:
                _LOGGER.info ("Find a device with unit_code %s", self['d_home_unit'][0] + str(i+9))
                device_found.append(self['d_home_unit'][0] + str(i+9))
        
    else:
        _LOGGER.debug (self)
        _LOGGER.debug("receive %s, for unit %s", self['d_command'], self['d_home_unit'])
        for entity in PlcbusSwitchList:
            if (entity._unit_code == self['d_home_unit']) :
                _LOGGER.debug("Device exists set status for %s", entity.name)
                if (self['d_command'] == "STATUS_ON") :
                    entity.set_state(True)
                elif (self['d_command'] == "STATUS_OFF") :
                    entity.set_state(False)
                elif (self['d_command'] == "ON") :
                    entity.set_state(True)
                elif (self['d_command'] == "OFF") :
                    entity.set_state(False)

def messageCB(self):
    _LOGGER.info ("messageCB")

def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.info("Setting up plcbus devices ", )

    device_name = config.get(CONF_DEVICE)
    Api = PLCBUSAPI(logging,device_name,commandCB,messageCB)
    user_code = config.get(CONF_USER_CODE)
    entities = []
    devices = config.get(CONF_UNIT)
    _LOGGER.info ("devices= %s",devices)
    for unit_code in map(chr, range(ord('A'), ord('K')+1)):
        _LOGGER.debug ("testing unit_code= %s",unit_code)
        Api.send("GET_ALL_ID_PULSE",unit_code,user_code)
    _LOGGER.debug ("device_found= %s",device_found)
    for device in devices:
        _LOGGER.info("device= %s",device)
        entities.append(PlcbusSwitch(Api, device, user_code, "mdi:electric-switch"))
    add_entities(entities, True)
    return True

class PlcbusSwitch(ToggleEntity):
    """Representation of a Plcbus switch."""

    def __init__(self,plcbus_API, unit_code, user_code, icon) -> None:
        """Initialize the Wifi switch."""
        self._name = "PlcbusSwitch_" + user_code + "_" + unit_code
        self._state = None
        self._plcbus_API = plcbus_API
        self._unit_code = unit_code
        self._user_code = user_code
        self._icon = icon
        self._unique_id = self._name
        PlcbusSwitchList.append(self)

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return f"{self._unique_id}"

    @property
    def icon(self) -> str:
        """Return the mdi icon of the entity."""
        return self._icon

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._state

    def set_state(self, state):
        """Turn the switch on or off."""
        self._state = state

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._plcbus_API.send("ON",self._unit_code,self._user_code)

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self._plcbus_API.send("OFF",self._unit_code,self._user_code)

    def update(self):
        """Get the state and update it."""
        self._plcbus_API.send("STATUS_REQUEST",self._unit_code,self._user_code)

