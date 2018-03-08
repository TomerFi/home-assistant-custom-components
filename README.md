# Home Assistant Custom Components

This repository contains various Custom Components I've made for use with [Home Assistant](https://home-assistant.io/).</br>

My current developing environment is HassIO 0.63.3.</br>

## My Custom Components TOC
- Domains
  - [date_notifier](/date_notifier/README.md) for managing yearly, monthly, daily and one time reminders and notifications.
- Platforms
  - switch
    - [switcher_heater](switcher_heater/README.md) for turning on or off your Switcher V2 water heater.
  - sensor
    - [shabbat_times](shabbat_times/README.md) for retrieving the Jewish Shabbat times from [hebcal](https://www.hebcal.com/).
	- [broadlink_s1c](broadlink_s1c/README.md) for integration with Broadlink's S1C Alarm Kit sensors.

## How do Custom Comoponents work in Home Assistant
There are two types of custom components for Home Assistant:</br>
- Platform components for existing domains like `switch` or `sensor`.</br>
- Domain components for integrating new domains.

Loading custom components is pretty straightforward as you can see in [this guide](https://home-assistant.io/developers/component_loading/).</br>
Basically, in you configuration folder (the same folder as `configuration.yaml`) you create a folder called `custom_components`.</br>
Everything within this folder is will be loaded to Home Assistant as components.</br>
To create a `domain` you can either save your `*.py` file in the root folder or create a new designated folder with a `__init__.py` file to represent your new domain.</br>
To create a `platform` for an existing domain, you create a folder named exactly like the `domain` you wrote the platform for and place your `*.py*` inside.</br>

Here is an example of the folder structure:
- `HA configuration folder/
  - custom_components/
    - *my_first_custom_domain.py*
	- my_second_custom_domain/
	  - *__init__.py*
	- sensor/
	  - *my_custom_sensor_platform.py*
	- switch/
	  - *my_custom_switch_platform.py*</br>`
	  
If you want to build your own components or maybe help improve some of mine,</br>
All you need to know in order to start doing so is in [this guide](https://home-assistant.io/developers/creating_components/).</br>

Feel free to `Watch` this repository as I plan to add more components and upgrading the existing ones constantly.</br>
If you like this repository you can even `Star` it. ;-)</br>
