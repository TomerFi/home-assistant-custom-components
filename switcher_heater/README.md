# Switcher V2 Boiler Switch</br>![Maintenance](https://img.shields.io/maintenance/no/2019.svg)

**NOT MAINTAINED!**

I'm no longer maintaining this custom component, you can use the new built in component [switcher_kis](https://www.home-assistant.io/components/switcher_kis/).

You can still use the files :point_up:, if you want.</br>
These :point_down: are the instructions.

__________________________________________

**Component Type** : `platform`</br>
**Platform Name** : `switcher_heater`</br>
**Domain Name** : `sensor`</br>
**Component Script** : [`custom_components/switcher_heater`](custom_components/switcher_heater)</br>

```
This is a new version of this component which includes:
- State updates
- Timer services
- Configuration services</br>
If you're upgrading from a previous version of this component,</br>
please note the entities naming change in the Special Notes section.</br>
```

[Community Discussion](https://community.home-assistant.io/t/switcher-v2-boiler-support-in-home-assistant/44318)</br>

#### Component Description
This custom component is based on the awesome script made available by **NightRang3r**, you can find the original script and the instruction on how to retrieve your device's information in Shai's repository [here](https://github.com/NightRang3r/Switcher-V2-Python).</br>

**Table Of Contents**
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Configuration Keys](#configuration-keys)
- [States](#states)
  - [State Attributes](#state-attributes)
- [Services](#services)
  - [Timer Services](#timer-services)
    - [Timer Service Calls Examples](#timer-service-calls-examples)
  - [Configuration Services](#configuration-services)
    - [Configuration Service Calls Examples](#configuration-service-calls-examples)
- [Logs](#logs)
- [Special Notes](#special-notes)
- [Credits](#credits)

## Requirements
- **Home Assistant version 0.88.0 or higher**.
- Your switcher device needs to have a **Static IP Address** reserved by your router.
- Please follow [Shai's instructions](https://github.com/NightRang3r/Switcher-V2-Python#requirements) and **gather the following information**:
  - phone_id
  - device_id
  - device_pass

## Installation
- Copy files [`custom_components/switcher_heater`](custom_components/switcher_heater) to your `ha_config_dir/custom_components/switcher_heater` directory.
- Configure like instructed in the Configuration section below.
- Restart Home-Assistant.

## Configuration
To use this component in your installation, add the following to your `configuration.yaml` file, supports multiple devices:

```yaml
# Example configuration.yaml

switch:
  - platform: switcher_heater
    switches:
      your_device_name:
        local_ip_addr: xxx-xxx-xxx-xxx
        phone_id: "xxxx"
        device_id: "xxxxxx"
        device_password: "xxxxxxxx"
        friendly_name: "your device friendly name" 
        scan_interval: 20
        icon: "your local or mdi icon"
```

### Configuration Keys
- **local_ip_addr** (*Required*): The IP Address assigned to your device by your router. A static address is preferable.</br>
- **phone_id** (*Required*): Your phone id.
- **device_id** (*Required*): Your desiered device id.
- **device_password** (*Required*): Your device password.
- **friendly_name** (*Optional*): A string representing the friendly name of your device, `default="SwitcherV2 Device"`.
- **scan_interval** (*Optional*): An integer representing the scan interval for the device, a minimum of 20 seconds is allowed, `default=20`.
- **icon** (*Optional*): A string representing the display icon for the switch.</br>

## States
Available states are:
- **on** Inherited from homeassistant.const.STATE_ON
- **off** Inherited from homeassistant.const.STATE_ON</br>

Please note, when the device in not reachable, Home Assistant will mark the switch as `unavailable`. If it's a momentary issue, it will be resolved with the next scan, if not, please check your logs for any errors.</br>

### State Attributes
These following state attributes are available in all states:
- **scan_interval**: the scan interval retrieving the date from the device.
- **ip_address**: the ip address of the device.
- **auto_off_configuration** - the configured auto-shutdown limit of the device.</br>

These following state attributes are available in `on` state only:
- **current_power_watts**: the current power consumption in watts.
- **current_power_amps**: the current power consumption in amps.
- **auto_off_time_left**: the time left till auto-shutdown.</br>

## Services
### Timer Services
There are four timer services:
- **switch.switcher_heater_turn_on_15_minutes**
- **switch.switcher_heater_turn_on_30_minutes**
- **switch.switcher_heater_turn_on_45_minutes**
- **switch.switcher_heater_turn_on_60_minutes**</br>

All four timer services allow turning on the device with a specific off timer, takes the following arguments:
- **entity_id** (Mandatory): allows 1 entity id or a List of entity id's
- **notify_service_name** (Optional):, a notification service to which the component will send turn on and off messages.</br>

#### Timer Service Calls Examples
```json
{
  "entity_id": "switch.your_device_name",
  "notify_service_name": "notify.my_notification_service_name"
}

{
  "entity_id": ["switch.your_device_name", "switch.your_second_device_name"],
  "notify_service_name": "notify.my_notification_service_name"
}

{
  "entity_id": "switch.your_device_name"
}

{
  "entity_id": ["switch.your_device_name", "switch.your_second_device_name"]
}
```

### Configuration Services
There is one configuration service:
- **switch.switcher_heater_set_auto_off*</br>

The service allows the configuring of the device `Auto-Shutdown` option for limiting the time your device can be `on`, takes the following arguments:
- **entity_id** (Mandatory): allows 1 entity id or a List of entity id's
- **auto_off** (Mandatory): allows to set hours and minutes only, seconds passed to the service will be ignored. minimum time allowed is 01:00 and maximum time is 23:59. </br>

#### Configuration Service Calls Examples
```json
{
  "entity_id": "switch.your_device_name",
  "auto_off": "01:00"
}

{
  "entity_id": "switch.your_device_name",
  "auto_off": "23:59"
}
```

## Special Notes
- If you’re upgrading this component from a previous version of it, PLEASE NOTE: The entity id is now based on the device id and not it's friendly name. Update your frontend accordingly.
- The use of multiple devices is supported.</br>

## Logs
The component provides standard log messages for the [Logger Component](https://home-assistant.io/components/logger/), `Warning` and `Error` is visible in `info` panel in Home Assistant. For `Debug` logs that will show up in you `.log file` please add the following to your `Logger` configuration:</br>
```yaml
custom_components.switch.switcher_heater: debug
```

Example working configrations:</br>
```yaml
logger:
  default: error
  logs:
    custom_components.switch.switcher_heater: debug
```

## Credits
- A script by **NightRang3r**, [here](https://github.com/NightRang3r/Switcher-V2-Python).
