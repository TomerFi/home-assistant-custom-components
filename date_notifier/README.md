# Date Notifier
**Component Type** : `domain`</br>
**Domain Name** : `date_notifier`</br>
**Component Script** : [`custom_components/date_notifier.py`](custom_components/date_notifier.py)</br>

##### Component Description
This component is called *date_notifier* and it is dependent on the **notify component**, it's used for creating reminders based on dates and times.</br>
Before using this component, please configure notifications using the [**notify component**](https://home-assistant.io/components/notify/) instructions.</br>
The **Date Notifier Component** supports four types of reminders:
- Yearly recurring reminder
- Monthly recurring reminder
- Daily recurring reminder
- One Time non-recurring reminder

**Table Of Contents**
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Configuration Keys](#configuration-keys)
- [States](#states)
- [Special Notes](#special-notes)

## Requirements
- A configured [**notify component**](https://home-assistant.io/components/notify/).

## Installation
- Copy file [`custom_components/date_notifier.py`](custom_components/date_notifier.py) to your `ha_config_dir/custom_components` directory.
- Configure like instructed in the Configuration section below.
- Restart Home-Assistant.

## Configuration
There are four type of reminders, yearly, monthly, daily and one time reminders.</br>
The type of reminder is decided based on the configuration variables.</br>

```yaml
# Example configuration.yaml

date_notifier:
  one_time_reminder1: # One Time Reminder will be send 1 day before the event date, on date 2017-11-19 at 21:25
    name: "one-time test"
    hour: 21
    minute: 25
    day: 20
    month: 11
    year: 2017
    message: "one-time test"
    days_notice: 1
    notifier: "ios_tomers_iphone6s"
  yearly_reminder: # Yearly Reminder will be send 2 days before the event date every year, on November 19th at 21:26
    name: "yearly test"
    hour: 21
    minute: 26
    day: 21
    month: 11
    message: "yearly test"
    days_notice: 2
    notifier: "ios_tomers_iphone6s"
  monthly_reminder: # Monthly Reminder will be send on the 19th of every month at 21:27
    name: "montly test"
    hour: 21
    minute: 27
    day: 19
    message: "montly test2"
    notifier: "ios_tomers_iphone6s"
  daily_reminder: # Daily Reminder will be send every day at 21:28
    name: "daily test"
    hour: 21
    minute: 28
    message: "daily test"
    notifier: "ios_tomers_iphone6s"
```

### Configuration Keys
**The following configuration variables are required for any reminder, use only the following for configuring a daily reminder:**
- **name** (*Required*): Any string representing the name of the reminder.
- **hour** (*Required*): A **positive integer between 0 and 23** representing the hour of the notification arrival.
- **minute** (*Optional*): A **positive integer between 0 and 59** representing the minute of the notification arrival. (default = 0)
- **message** (*Required*): Any string representing the message for the notification, the message will concatenated with a predefined text representing the number of days to the event.
- **notifier** (*Required*): A valid *notifier name* to be used as the recipient of the notification.

**The following configuration variable is optional, add the following to all of previous for configuring a monthly reminder:**
- **day** (*Optional*): A **positive integer between 1 and 31** representing the day for a monthly reminder. (default = None)

**The following configuration variable is optional, add the following to all of previous for configuring a yearly reminder:**
- **month** (*Optional*): A **positive integer between 1 and 12** representing the month for a yearly reminder. (default = None)

**The following configuration variable is optional, add the following to all of previous for configuring a one time reminder:**
- **year** (*Optional*):  A **positive 4 digits integer** representing the year for a one time reminder. (default = None)

**The following configuration variable is optional and eligible when configuring a monthly, yearly or one time reminders:**
- **days_notice** (*Optional*): A **positive integer** representing the number of days before the date in which the notification will be send. (default = 0)

## States
Each reminder will create it's own entity with the configuration variables as state attributes, there are five potential states:
- *daily*: for daily reminders.
- *monthly*: for monthly reminders.
- *yearly*: for yearly reminders.
- *on_date*: for future one time reminders.
- *past_due*: for past one time reminders.

## Special Notes
- In future releases I plan on adding another configure variable of Boolean type called *countdown*, when true reminders with a *days_notice* variable bigger then 0, will launch a "countdown" everyday starting with the *days_notice* limit and ending at the day of the event.
- In future releases I plan on adding a service for reloading the configuration, for now, when editing any active reminders or adding new ones, a Home Assistant restart is required.
