# Home-Assistant Custom Components

Custom components I made for use with [home-assistant hass.io](http://www.home-assistant.io).

## Shabbat Times Custom Sensor

This componet acts as a new platform called *shabbat_times* for the *sensor* domain.
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
