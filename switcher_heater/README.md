# Switcher V2 Bolier Switch
**Component Type** : `platform`</br>
**Platform Name** : `switcher_heater`</br>
**Domain Name** : `sensor`</br>
**Component Script** : [`custom_components/switch/switcher_heater.py`](custom_components/switch/switcher_heater.py)</br>

[Community Discussion](https://community.home-assistant.io/t/switcher-v2-boiler-support-in-home-assistant/44318)</br>

#### Component Description
This custom component is based on the awesome script made available by **NightRang3r**, you can find the original script and the instruction on how to retrieve your device's information in Shai's repository [here](https://github.com/NightRang3r/Switcher-V2-Python).</br>

**Table Of Contents**
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Configuration Keys](#configuration-keys)
- [Credits](#credits)

## Requirements
- **Home Assistant version 0.62 or higher**.
- Your switcher device needs to have a **Static IP Address** reserved by your router.
- Please follow [Shai's instructions](https://github.com/NightRang3r/Switcher-V2-Python#requirements) and **gather the following information**:
  - phone_id
  - device_id
  - device_pass

## Installation
- Copy file [`custom_components/switch/switcher_heater.py`](custom_components/switch/switcher_heater.py) to your `ha_config_dir/custom_components/switch` directory.
- Configure like instructed in the Configuration section below.
- Restart Home-Assistant.

## Configuration
To use this component in your installation, add the following to your `configuration.yaml` file, supports multiple devices:

```yaml
# Example configuration.yaml

switch:
  - platform: switcher_heater
    switches:
      device1:
        friendly_name: "heater_switch"
        local_ip_addr: 'XXX.XXX.XXX.XXX'
        phone_id: 'XXXX'
        device_id: 'XXXXXX'
        device_password: 'XXXXXXXX'
```

### Configuration Keys
- **friendly_name** (*Required*): A string representing the friendly name of your device.
- **local_ip_addr** (*Required*): The IP Address assigned to your device by your router. A static address is preferable.</br>

*The following was retrieved based on NightRang3r original instructions*:
- **phone_id** (*Required*): Your phone id.
- **device_id** (*Required*): Your device id.
- **device_password** (*Required*): Your device password.</br>

## Credits
- A script by **NightRang3r**, [here](https://github.com/NightRang3r/Switcher-V2-Python).
