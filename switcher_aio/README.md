# Switcher V2 All-In-One
**Component Type** : `domain`</br>
**Domain Name** : `switcher_aio`</br>
**Component Script** : [`custom_components/switcher_aio`](custom_components/switcher_aio)</br>

[Video Tutorial](https://youtu.be/NbxRCARx168)</br>
[Community Discussion](https://community.home-assistant.io/t/switcher-v2-all-in-one-full-control/50652)</br>

#### Component Description
This custom component is based on the awesome script made available by **NightRang3r** and **AviadGolan**, you can find the original script and the instruction on how to retrieve your device's information in Shai's repository [here](https://github.com/NightRang3r/Switcher-V2-Python).</br>
This component offers a full integration with the *Switcher V2 Water Heater*, with real-time updates of the data from the device.</br>
Current functionalities are:
- Retrieving all the data from the device: state, power consumption, schedules, configuration and so on.
- Turning the device on or off.
- Turning the device on with 15, 30, 45 or 60 minutes timer.
- Calling a notification service on state changes.
- Changing the device name.
- Configuring the device's auto-off time.
- Enabling, disabling, deleting and creating schedules.

**Table of Contents**
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Configuration Keys](#configuration-keys)
- [Services](#services)
- [Entities](#entities)
- [Logs](#logs)
- [Credits](#credits)

## Requirements
- **Home Assistant version 0.62 or higher**.
- Please follow [Shai and Aviad's instructions](https://github.com/NightRang3r/Switcher-V2-Python) and **gather the following information**:
  - phone_id
  - device_id
  - device_pass

## Installation
- Create a new folder called *switcher_aio* inside your `ha_config_dir/custom_components` directory and copy the all the files from [`custom_components/switcher_aio`](custom_components/switcher_aio) to it.
- Configure like instructed in the Configuration section below.
- Restart Home-Assistant.

## Configuration
To use this component in your installation, add the following to your `configuration.yaml` file, supports multiple devices:

```yaml
# Example of the mandatory fields in configuration.yaml

switcher_aio:
  phone_id: xxxx
  device_id: xxxxxx
  device_password: xxxxxxxx
```
```yaml
# Example of the mandatory and optional fields in configuration.yaml

switcher_aio:
  phone_id: xxxx
  device_id: xxxxxx
  device_password: xxxxxxxx
  create_view: true
  create_groups: true
  schedules_scan_interval:
    minutes: 5
```

### Configuration Keys
- **phone_id** (*Required*): Your phone id.
- **device_id** (*Required*): Your device id.
- **device_password** (*Required*): Your device password.
- **create_view** (*Optional*): Boolean indicating rather or now the component should create its own view, `default=true`.
- **create_groups** (*Optional*): Boolean indicating rather or now the component should create its own groups, `default=true`.
- **schedules_scan_interval** (*Optional*) Timedelta dictionary for setting the interval between schedules retrieval from the device. Please note, this setting effects only the schedules retrieval, all the other data is being retrieved in real-time.</br>
Please note, some of the components entities is more efficient if it can retrieve the previous states after a system restart, therefore it is highly recommended to allow *HA* to remember the states of the component with the [recorder component](https://www.home-assistant.io/components/recorder/), here is an example of a working configuration:</br>
```yaml
# configuration.yaml

recorder:
  purge_interval: 2
  purge_keep_days: 7
  include:
    domains:
      - switcher_aio
```

## Services
The component creates 12 services:
- **switcher_aio.turn_on** *service* from turning on the various component switches, takes the following arguments:
  - **entity_id** - name(s) of switcher entities to turn on. `Example: ["switcher_aio.control_device_switch"]`
- **switcher_aio.turn_off** *service* from turning off the various component switches, takes the following arguments:
  - **entity_id** - name(s) of switcher entities to turn off. `Example: ["switcher_aio.control_device_switch"]`
- **switcher_aio.turn_on_15_minutes** *service* to turn on the device with a timer of 15 minutes, takes no arguments.
- **switcher_aio.turn_on_30_minutes** *service* to turn on the device with a timer of 30 minutes, takes no arguments.
- **switcher_aio.turn_on_45_minutes** *service* to turn on the device with a timer of 45 minutes, takes no arguments.
- **switcher_aio.turn_on_60_minutes** *service* to turn on the device with a timer of 60 minutes, takes no arguments.
- **switcher_aio.set_auto_off** *service* to update the device configuration for auto-off time, takes the following arguments:
  - **auto_off** time period string containing hours and minutes. `Example: "02:30"`
- **switcher_aio.update_device_name** *service* to update the device's name, takes the following arguments:
  - **name** any string with the minimum length of 2 and the maximum length of 32. `Example: "My Switcher Device"`
- **switcher_aio.delete_schedule** *service* for deleting a specific schedule, takes the following arguments:
  - **schedule_id** integer identifier of the schedule to be deleted, minimum value is 0, maximum value is 7. `Example: 3`
- **switcher_aio.disable_schedule** *service* for disabling a specific schedule, takes the following arguments:
  - **schedule_id** integer identifier of the schedule to be disabled, minimum value is 0, maximum value is 7. `Example: 3`
- **switcher_aio.enable_schedule** *service* for enabling a specific schedule, takes the following arguments:
  - **schedule_id** integer identifier of the schedule to be enabled, minimum value is 0, maximum value is 7. `Example: 3`
- **switcher_aio.create_schedule** *service* for creating schedules, takes the following arguments:
  - **start_time** time string containing hours and minutes representing the time to start the schedule. `Example: "13:45"`
  - **end_time** time string containing hours and minutes representing the time to end the schedule. `Example: "13:45"`
  - **recurring** boolean indicating if the schedule is recurring (true) or is it to be executed once (false). `Example: true`
  - **days** same(s) of the days for the schedule to run in, this is an optional field that must be passed if recurring=true. Possible values are: Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday. `Example: "Monday", "Wednesday", "Saturday"`</br>

## Entities
The component creates the following entities:
- **group.switcher_aio_v2_view** *view* gathering the following groups:
  - **group.switcher_aio_v2_control** *group* for gathering entities for controlling the device:
    - **switcher_aio.control_device_switch** *switch* turning the device on or off using the services *switcher_aio.turn_on* and *switcher_aio.turn_off*.
    - **switcher_aio.time_left_sensor** *sensor* indicating time left until the device automaticlly turns off.
    - **switcher_aio.electric_current_sensor** *sensor* indicating the electric current in amps.
    - **switcher_aio.device_name_sensor** *sensor* indicating the device's name.
    - **switcher_aio.auto_off_sensor** *sensor* indicating the time limit for the auto-off configuration of the device.
    - **switcher_aio.timer_minutes_input_select** *input_select* for selecting minutes to be sent as timer, 15, 30, 45 or 60 minutes.
    - **switcher_aio.turn_on_timer_script** *script* calling one of the following services based on the option selected in the previous input_select, *switcher_aio.turn_on_15_minutes*, *switcher_aio.turn_on_30_minutes*, *switcher_aio.turn_on_45_minutes* or *switcher_aio.turn_on_60_minutes*.
  - **group.switcher_aio_v2_configuration** *group* for gathering entities for configuring the device:
    - **switcher_aio.notification_service_input_select** *input_select* containing all the registered *notify* services on you *ha*, the service selected will receive notifications each time the devices changes states (on>off, off>on).
    - **switcher_aio.set_auto_off_hours_slider** *input_number* for selecting the hours value to set as auto-off for the device.
    - **switcher_aio.set_auto_off_minutes_slider** *input_number* for selecting the minutes value to set as auto-off for the device.
    - **switcher_aio.send_auto_off_script** *script* concatinating the value from the two previous *input_number* entities and sending them as *auto_off* to the *switcher_aio.set_auto_off* service.
    - **switcher_aio.name_of_device_input_text* *input_text* for typing a new name for the device.
    - **switcher_aio.update_device_name_script** *script* sending the value from the previous *input_text* as *name* to the *switcher_aio.update_device_name*.
  - **group.switcher_aio_v2_schedules** *group* for gathering entities for managing the schedules of the devices:
    - **switcher_aio.schedule_for_action_input_select** *input_select* for selecting the id of the schedule you want to perform action on. The device only allowed 8 schedules with the id of 0-7.
    - **switcher_aio.action_to_perform_input_select** *input_select* for selecting the action to perform, Enable, Disable or Delete.
    - **switcher_aio.perform_schedule_action_script** *script* for calling one of the following services based on the value from the previous *input_select* entities: *switcher_aio.enable_schedule*, *switcher_aio.disable_schedule* or *switcher_aio.delete_schedule*.
    - **switcher_aio.schedule_id0_sensor** *sensor* indicating the state of the schedule at id 0.
    - **switcher_aio.schedule_id1_sensor** *sensor* indicating the state of the schedule at id 1.
    - **switcher_aio.schedule_id2_sensor** *sensor* indicating the state of the schedule at id 2.
    - **switcher_aio.schedule_id3_sensor** *sensor* indicating the state of the schedule at id 3.
    - **switcher_aio.schedule_id4_sensor** *sensor* indicating the state of the schedule at id 4.
    - **switcher_aio.schedule_id5_sensor** *sensor* indicating the state of the schedule at id 5.
    - **switcher_aio.schedule_id6_sensor** *sensor* indicating the state of the schedule at id 6.
    - **switcher_aio.schedule_id7_sensor** *sensor* indicating the state of the schedule at id 7.
  - **group.switcher_aio_v2_create_schedule** *group* for gathering the entities needed to create a new schedule:
    - **switcher_aio.set_schedule_start_time_input_text** *input_text* for typing the start time of the schedule.
    - **switcher_aio.set_schedule_end_time_input_text** *input_text* for typing the end time of the schedule.
    - **switcher_aio.select_sunday_input_boolean** *input_boolean* for selecting Sunday as a run day for the schedule.
    - **switcher_aio.select_monday_input_boolean** *input_boolean* for selecting Monday as a run day for the schedule.
    - **switcher_aio.select_tuesday_input_boolean** *input_boolean* for selecting Tuesday as a run day for the schedule.
    - **switcher_aio.select_wednesday_input_boolean** *input_boolean* for selecting Wednesday as a run day for the schedule.
    - **switcher_aio.select_thursday_input_boolean** *input_boolean* for selecting Thursday as a run day for the schedule.
    - **switcher_aio.select_friday_input_boolean** *input_boolean* for selecting Friday as a run day for the schedule.
    - **switcher_aio.select_saturday_input_boolean** *input_boolean* for selecting Saturday as a run day for the schedule.
    - **switcher_aio.create_schedule_script** *script* for wrapping all the values selected on the previous entities in this group to the *switcher_aio.create_schedule* service. Please note, if no *input_boolean* is selected, the schedule will be created as non-recurring, which means it'll only run once.</br>

## Logs
The component provides standard log messages for the [Logger Component](https://home-assistant.io/components/logger/), `Warning` and `Error` is visible in `info` panel in Home Assistant. For `Debug` logs that will show up in you `.log file` please add the following to your `logger` configuration:</br>
```yaml
custom_components.switcher_aio: debug
```

Example working configration:</br>
```yaml
# configuration.yaml

logger:
  default: error
  logs:
    custom_components.switcher_aio: debug
```

## Credits
- A script by **NightRang3r** and **AviadGolan**, [here](https://github.com/NightRang3r/Switcher-V2-Python).
