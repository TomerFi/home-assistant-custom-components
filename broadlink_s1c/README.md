# Broadlink S1C Alarm Kit Sensors</br>![Maintenance](https://img.shields.io/maintenance/no/2019.svg)

**NOT MAINTAINED!**

I'm no longer maintaining this custom component!</br>
That doesn't mean I don't use is, It just means this repository will not be maintained.

This custom component can be found in [my home assistant configuration](https://github.com/TomerFi/my_home_assistant_configuration).

You can still use the files :point_up:, if you want.</br>
These :point_down: are the instructions.

__________________________________________

**Component Type** : `platform`</br>
**Platform Name** : `broadlink_s1c`</br>
**Domain Name** : `sensor`</br>
**Component Script** : [`custom_components/broadlink_s1c`](custom_components/broadlink_s1c)</br>

[Community Discussion](https://community.home-assistant.io/t/broadlink-s1c-alarm-kit-custom-sensor-component/45980)</br>

#### Component Description
Home Assistant Custom Component for integration with [Broadlink S1C Alarm Kit](http://www.ibroadlink.com/s1c/).</br>
S1C Alarm Kit is a alarm system made by Broadlink, it's made of a Hub which can control up to 16 designated devices:
- Door/Window Sensor
- Motion Detector
- Key Fob

According to Broadlink's site, more sensor types are to released eventually.</br>
The uniqueness of this system is its integration with the rest of the Broadlink smart home products, for instance you can create an interaction as they call it, and make it so the your Broadlink TC2 switch will be turned on when the door sensor is open.</br>
But... If you're in this repository, You probably looking for a way to integrate this system with Home Assistant, so that last fact doesn't really matters.</br>
So, let's get to it! ;-)</br>

**Table Of Contents**
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Configuration Keys](#configuration-keys)
- [States](#states)
  - [All Sensors](#all-sensors)
  - [Door Sensor](#door-sensor)
  - [Motion Detector](#motion-detector)
  - [Key Fob](#key-fob)
- [Special Notes](#special-notes)
- [Credits](#credits)

## Requirements
- **Home Assistant version 0.88.0 or higher**.
- Your S1C Hub needs to have a **Static IP Address** reserved by your router.

## Installation
- Copy the files [`custom_components/broadlink_s1c`](custom_components/broadlink_s1c) to your `ha_config_dir/custom_components/broadlink_s1c` directory.
- Configure like instructed in the Configuration section below.
- Restart Home-Assistant.

## Configuration
To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml

sensor:
  - platform: broadlink_s1c
    ip_address: xxx.xxx.xxx.xxx
    mac: "xx:xx:xx:xx:xx:xx"
    timeout: 10
```

### Configuration Keys
- **ip_address** (*Required*) Inherited from *homeassistant.const.CONF_IP_ADDRESS*: The IP Address assigned to your device by your router. A static address is preferable.</br>
- **mac** (*Required*) Inherited from *homeassistant.const.CONF_MAC*: The MAC Address of your S1C Hub.</br>
- **timeout** (*Optional*) Inherited from *homeassistant.const.CONF_TIMEOUT*: Timeout value for S1C Hub connectio. *Default=10*.</br>

## States
### All Sensors
- `tampered`
- `unknown` - Inherited from *homeassistant.const.STATE_UNKNOWN*

### Door Sensor
- `open` - Inherited from *homeassistant.const.STATE_OPEN*
- `closed` - Inherited from *homeassistant.const.STATE_CLOSED*

### Motion Detector
- `no_motion`
- `motion_detected`

### Key Fob
- `disarmed` - Inherited from *homeassistant.const.STATE_ALARM_DISARMED*
- `armed_away` - Inherited from *homeassistant.const.STATE_ALARM_ARMED_AWAY*
- `armed_home` - Inherited from *homeassistant.const.STATE_ALARM_ARMED_HOME*
- `sos`

## Special Notes
- Initial configuration of the sensor in the Broadlink App is required.
- The platform discovers the sensors upon loading, therefore if you add another sensor, restart Home Assistant and the new sensors will be added to ha.
- The entity name of each sensor is constructed from the original sensor name from the Broadlink App concatenated with the platform name. Spaces and dashes will be replaced with underscores.</br>
  For instance, if you sensor is name *Bedroom Door* the entity name will be *broadlink_s1c_bedroom_door*, and to reference it you will call *sensor.broadlink_s1c_bedroom_door*
- The custom component used a tweaked version of the *python-broadlink* library from a [forked repository](https://github.com/TomerFi/python-broadlink) of it on my GitHub.
- Although this component is designed for S1C Hubs, users report it to be working well with S2C Hubs too.

## Credits
- A script by **NightRang3r**, [here](https://community.home-assistant.io/t/broadlink-s1c-kit-sensors-in-ha-using-python-and-mqtt/19886).
- The *python-broadlink* library made by **mjg59**, [here](https://github.com/mjg59/python-broadlink).
