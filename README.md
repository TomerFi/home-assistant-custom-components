# Home-Assistant Custom Components

Custom components I made for use with [home-assistant hass.io](http://www.home-assistant.io).

## Shabbat Times Custom Sensor

This component acts as a new platform called *shabbat_times* for the *sensor* domain.
The component works in a simillar manner as the *rest* type sensor, it send an api request towards [Hebcal's Shabbat Times API](https://www.hebcal.com/home/197/shabbat-times-rest-api) and retrievs the **next** or **current** shabbat start and end date and time, and sets them as attributes within a created sensor.</br>
The component can create multiple sensors for multiple cities around the world, the selected city is identified by its geoname which can selected [here](https://github.com/hebcal/dotcom/blob/master/hebcal.com/dist/cities2.txt).

### Installation

- Copy file [`custom_components/sensor/shabbat_times.py`](custom_components/sensor/shabbat_times.py) to your `ha_config_dir/custom_components/sensor` directory.
- Configure with config below.
- Restart Home-Assistant.

## Usage
To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml

sensor:
  - platform: shabbat_times
    geonames: VALID_GEONAME
```

Configuration variables:

- **geonames** (*Required*): A valid geoname selected [here](https://github.com/hebcal/dotcom/blob/master/hebcal.com/dist/cities2.txt), multiple geonames seperated by a comma is allowed.
- **candle_lighting_minutes_before_sunset** (*Optional*): Minutes to subtract from the sunset time for calculation of the candle lighting time. (default = 30)
- **havdalah_minutes_after_sundown** (*Optional*): Minutes to add to the sundown time for calculation of the shabbat end time. (default = 42)
- **scan_interval** (*Optional*): Seconds between updates. (default = 60)

Working Configuration Example:

```yaml
# Example configuration.yaml

sensor:
  - platform: shabbat_times
    geonames: "IL-Haifa,IL-Rishon LeZion"
    candle_lighting_minutes_before_sunset: 0
    havdalah_minutes_after_sundown: 40
```
This configuration will create two sensors:
- *sensor.shabbat_times_il_haifa*
- *sensor.shabbat_times_il_rishon_lezion*

Each sensor will have its own set of attributes:
- *shabbat_start*
- *shabbat_end*

Which will be calulated based on configration optional values **candle_lighting_minutes_before_sunset** and **havdalah_minutes_after_sundown**.
These attributes are available for use within templates like so:
- *{{ states.sensor.shabbat_times_il_haifa.attributes.shabbat_start }}* will show the shabbat start date and time in Haifa.
- *{{ states.sensor.shabbat_times_il_rishon_lezion.attributes.shabbat_end }}* will show the shabbat end date and time in Rishon Lezion.

Sensor States:

The created sensors has 4 possible states:
- *Awaiting Update*: the sensor hasn't been updated yet.
- *Working*: the sensor is being updated at this moment.
- *Error...*: the api has encountered an error.
- *Updated*: the sensor has finished updating.

Any state besides *Updated* is rarely used and will probably add an error message in home assistant's logs. If so, please check the log and try to correct the error if its source is in the configration parameters. If a code modification is required please create a new issue.

**Special Note**: The sensors will allways show the date and time for the next shabbat, unless the shabbat is now, and therefore the sensors will show the current shabbat date and time.

## Date Notifier Custom Component

This component is called *date_notifier* and it is dependent on the **notify component**, it's used for creating reminders based on dates and times.</br>
Before using this component, please configure notification using the [**notify component**](https://home-assistant.io/components/notify/) instructions.
The **Date Notifier Component** supports four types of reminders:
- Yearly recurring reminder
- Monthly recurring reminder
- Daily recurring reminder
- One Time non-recurring reminder

### Installation

- Copy file [`custom_components/date_notifier.py`](custom_components/date_notifier.py) to your `ha_config_dir/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

## Usage
There are four type of reminders, yearly, monthly, daily and one time reminders.</br>
The type of reminder is decided based on the configuration variables.</br>

**The following configuration variables are required for any reminder, use only the following for configuring a daily reminder:
- **name** (*Required*): Any string representing the name of the reminder.
- **hour** (*Required*): A **positive integer between 0 and 23** represnting the hour of the notification arrival.
- **minute** (*Optional*): A **positive integer between 0 and 59** represnting the minute of the notification arrival (default = 0).
- **message** (*Required*): Any string representing the message for the notification, the message will concatenated with a predefined text represnting the number of days to the event.
- **notifier** (*Required*): A valid *notifier name* to be used as the recipient of the notification.

**The following configuration variable is optional, add the following to all of previous for configuring a monthly reminder:
- **day** (*Optional*): A **positive integer between 1 and 31** represnting the day for a monthly reminder (default = None).

**The following configuration variable is optional, add the following to all of previous for configuring a yearly reminder:
- **month** (*Optional*): A **positive integer between 1 and 12** represnting the month for a yearly reminder (default = None).

**The following configuration variable is optional, add the following to all of previous for configuring a one time reminder:
- **year** (*Optional*):  A **positive 4 digits integer** represnting the year for a one time reminder (default = None).

**The following configuration variable is optional and eligible when configuring a monthly, yearly or one time reminders:
- **days_notice** (*Optional*): A **postive integer** represnting the number of days before the date in which the notification will be send (default = 0).

Working Configuration Example:

```yaml
# Example configuration.yaml

date_notifier:
# One Time Reminder will be send 1 day before the event date, on date 2017-11-19 at 21:25
  one_time_reminder:
    name: "one-time test"
    hour: 21
    minute: 25
    day: 20
    month: 11
    year: 2017
    message: "one-time test"
    days_notice: 1
    notifier: "ios_tomers_iphone6s"

# Yearly Reminder will be send 2 days before the event date every year, on November 19th at 21:26
  yearly_reminder:
    name: "yearly test"
    hour: 21
    minute: 26
    day: 21
    month: 11
    message: "yearly test"
    days_notice: 2
    notifier: "ios_tomers_iphone6s"

# Monthly Reminder will be send on the 19th of every month at 21:27
  monthly_reminder:
    name: "montly test"
    hour: 21
    minute: 27
    day: 19
    message: "montly test2"
    notifier: "ios_tomers_iphone6s"
  
# Daily Reminder will be send every day at 21:28
  daily_reminder:
    name: "daily test"
    hour: 21
    minute: 28
    message: "daily test"
    notifier: "ios_tomers_iphone6s"
```
Based on this configuration, I've received four notifications withing four minutes, you can see the received notifications [here]().

**Entity States**
Each reminder will create it's own entity with the configuration variables as state attributes, there are five potential states:
- *daily*: for daily reminders.
- *monthly*: for monthly reminders.
- *yearly*: for yearly reminders.
- *on_date*: for future one time reminders.
- *past_due*: for past one time reminders.

**Special Notes**:
- This component is dependent on the **notify component**, before using this component, please configure notification using the [**notify component**](https://home-assistant.io/components/notify/) instructions.
- In future releases I plan on adding another configure variable of boolean type called *countdown*, when true reminders with a *days_notice* variable bigger then 0, will launch a "countdown" everyday starting with the *days_notice* limit and ending at the day of the event.
- In future releases I plan on adding a service for relaoding the configuration, for now, when editing any active reminders or adding new ones, a Home Assistant restart is required.
