# E-paper Infoscreen

Inkplate 10 using ESP32, ESP-IDF, 16 MB flash, a PCF85063 RTC, and Home Assistant
sensor imports. The initial configuration was read from
`/root/config/esphome/e-paper-infoscreen.yaml` on 2026-09-19 and matched the
user-provided source. The original baseline is preserved in Git history.
The current configuration includes the user's live change disabling display capture.

## Included dependencies

- `fonts/materialdesignicons-webfont.ttf`: existing live Material Design Icons font.
- Three images in `images/`, copied from the exact files referenced by the live YAML.
- Inter fonts are fetched through ESPHome's `gfonts://` references.
- Remote screenshot capture (`display_capture`) and its external component source
  are commented out. The user disabled this optional feature after its obsolete
  `request->url()` calls failed to compile against ESPHome 2026.9.0.
  The commented source reference remains for history; it is not an active dependency.
- Commented Helvetica font examples are inactive and their files are not included.

Assets retain their original ownership and licensing; no new repository-wide
license is assigned by this import.

## Credentials

Use the adjacent `secrets.example.yaml` as the local template. The API key and OTA
password references replace inline credentials from the live file; a commented
fallback access-point password has also been replaced. Do not change the actual
device credentials as part of importing this repository.

## Boot and loading behavior

- On a cold boot (power-on or reset) the welcome page (`ss_logo`) is drawn first.
- The weather page is only drawn once `weather_data_ready` is true: current
  temperature, first hourly temperature, hot tub temperature, current conditions
  and the first hourly time label have all arrived from Home Assistant.
  `on_boot` waits up to 120 s for that, then runs `mainLoop`.
- Deep-sleep wakeups do not redraw the welcome page; the previous weather screen
  stays up until fresh data is in.
- Any number that is still missing renders as `--` instead of `nan`.
- The `input_button.refresh_forecast` trigger runs `mainLoop`, but its first value
  after connecting is ignored so it cannot draw a half-loaded page.

- Refreshes are partial (only changed pixels redraw, no black/white flash).
  The "Inkplate Partial Updating" template switch is `restore_mode: ALWAYS_ON`;
  the template-switch default (`ALWAYS_OFF`) used to disable partial updates on
  every boot. One full refresh runs nightly at 3:00 to clear ghosting.
- The footer shows the date, not a clock, so the page only changes when data
  does. If HA is unreachable for 30+ minutes the footer reads "offline since …".
- Deep-sleep wakeups keep quiet partial updates: the driver saves its copy of
  the panel image to flash before sleeping and restores it on wake (see
  "Battery and deep sleep").

## Screen layout (2026-11-19)

- **Header (fixed):** current conditions icon and temperature, "feels like",
  and the day's outlook — **Today** until 5 PM, then **Tomorrow** — with
  conditions, chance of precipitation, high/low and wind. Logo on the right.
- **Body (rotates every 10 minutes):** only through pages whose data is
  available. Today = AI 8-hour forecast + next five hours; 5-day forecast.
  Seasonal pages (ski, snowmobile, Santa's Village, hiking) will be added with
  eligibility computed in Home Assistant.
- **Footer (fixed):** spa temperature, setpoint and heating/pump/light/filter
  icons, page dots, the date (or "offline since …").

To add a page: bump `NUM_PAGES` and add its eligibility check in both the
`weather_page1` lambda (`page_ok[]`) and the 10-minute rotation interval, then
add its body block.

## Main floor motion and refresh modes

`binary_sensor.mountain_house_motion` (the main thermostat's HomeKit motion
sensor, the floor the frame is on) decides how the screen refreshes:

- **Someone on the main floor in the last hour:** redraws every minute as
  quiet partial updates; walking in triggers an immediate redraw.
- **Nobody for an hour:** the minute redraws are skipped; the 10-minute page
  changes (and button presses) use a full refresh, which clears ghosting.
- The first weather draw after a reboot is always a full refresh, so the
  welcome screen leaves no ghost.

A **Next page** button entity steps to the next page immediately.

## Data sources (2026-11-19)

- Current conditions: Weather Underground station `weather.knhlanca3` and its
  `sensor.knhlanca3_*` sensors (dew point replaces the old cloud ceiling line;
  precipitation is the live rain rate).
- Hot tub: `climate.stargazer_s_spa_thermostat_1` — `current_temperature` and the
  `temperature` (target) attribute, which replaced the old `hvac_action` read
  that always produced `nan`.
- 8-hour text forecast: `sensor.chatgpt_forecast_8_hours`, `forecast` attribute.

## Verified build

On 2026-09-19, the live configuration with display capture disabled successfully
compiled using ESPHome 2026.9.0 and ESP-IDF 5.5.5 in the existing Home Assistant
ESPHome container. This was a compile-only test; no firmware was uploaded.

- Reported flash usage: 1,453,187 bytes (17.9% of the application partition).
- Reported static DRAM usage: 54,856 bytes (30.4%); this is not runtime heap usage.
- Generated `firmware.ota.bin`, `firmware.factory.bin`, and `firmware.elf` under
  `/config/esphome/.esphome/build/e-paper-infoscreen/build/` inside the container.
- Remaining non-fatal warnings concern the older image configuration format,
  GPIO12, the OTA password, and the remote transmitter's default blocking mode.
- Sensor data and physical display behavior still need runtime verification.

## Deployment

Only the live `e-paper-infoscreen.yaml` is within the current remote write scope.
Fonts and images were copied locally. Their live counterparts must not be changed. See the repository README for handling secret references and keeping
other ESPHome projects untouched.

## Battery and deep sleep (2026-11-19)

Runs from a 10,000 mAh LiPo behind the frame. Home Assistant decides the power
mode; the frame reads it on every pass of `mainLoop`.

| Mode | When | Frame does |
|---|---|---|
| awake | daytime, or anyone around | slideshow as above, never sleeps |
| night | 8 PM - 10 AM and every occupancy/motion sensor off | 5-day forecast, deep sleep 30 min, check again; any occupancy resumes the slideshow |
| vacant | no stay for 1 h after checkout, until 3 h before the next arrival | welcome screen, deep sleep up to 6 h |

HA helpers (UI template / derivative helpers):

- `sensor.e_ink_power_mode`: awake / night / vacant. Uses
  `sensor.mountainhouse_active_stay` (House Observer) for vacancy and the
  ecobee occupancy sensors (main, upstairs, basement, garage) plus
  `binary_sensor.house_motion` for night.
- `sensor.e_ink_sleep_seconds`: 1800 at night; vacant sleeps until 3 h before
  `next_arrival`, 10 min to 6 h per sleep.
- `input_boolean.e_ink_stay_awake`: forces awake. **Turn it on before an OTA
  update** (a sleeping frame can't be flashed) and wait up to 30 min.
- `input_boolean.e_ink_sleep_mode`: forces vacant (hibernate).
- Battery: `sensor.e_ink_battery_drain` (%/day over 12 h),
  `sensor.e_ink_battery_days_left`, `binary_sensor.e_ink_battery_charging`.

Frame side:

- Before deep sleep the driver PackBits-compresses its copy of the panel image
  (`buffer_`, 123,750 bytes 1-bit, usually a few KB compressed) into NVS; on a
  deep-sleep wake it restores it, so redraws diff against what is really on the
  glass. That is what the earlier `inkplatedisplay_sleep_buffer` experiment was
  missing: PSRAM is powered down in deep sleep, so keeping the buffers allocated
  did not keep their contents, and partial updates diffed against a blank
  buffer. Code: `components/inkplate/frame_store.cpp` (external component, a
  copy of ESPHome 2026.10.2's `inkplate` plus this file).
- Night redraws are quiet partial updates; one full refresh on the 3 AM wake.
- Woke from a timer but no HA for 3 minutes: sleeps again 30 min.
- Battery % now averages 8 ADC samples per reading and caps at 100% instead of
  dropping readings (it used to sit at "unknown" while charging).

Buttons (both flip the page and wake the frame; a press keeps it awake 10 min):

- Onboard WAKE button, GPIO36.
- Frame button: momentary switch from **IO39** to **GND**. IO39 is shared with
  the RTC interrupt line (jumper JP2, connected by default), which has the
  board's pull-up and isn't used by this config. IO34-39 have no internal
  pull-ups; if the "Frame button" entity flickers with nothing pressed, add a
  10 kOhm pull-up from IO39 to 3.3 V. The frame button only arms as a wake
  source when the line reads high, so a stuck line can't cause a wake loop.

IR blaster: `remote_transmitter` on **GPIO13**. GPIO12 is a boot strapping pin
(held high at power-on it stops the ESP32 booting). GPIO12-15 are the microSD
slot's pins, so the SD card is not used. An IR LED needs a transistor driver
(e.g. 2N2222 or an N-MOSFET with a 22-47 Ohm series resistor from 3.3-5 V);
the GPIO alone gives very little range.

## Seasonal pages (2026-11-19)

Body pages rotate every 10 minutes through the ones that are in season:

| # | Page | Shown when |
|---|---|---|
| 0 | Today: AI 8-hour forecast + next five hours | always |
| 1 | 5-day forecast | forecast loaded |
| 2 | Hikes near the house | under 1 in of snow at the house |
| 3 | Santa's Village | open later today or in the next 3 days |

- **Hikes:** the 17 hikes on our AllTrails list (the paddling trail is left
  out), nearest first by drive time from the house, six per set. Each visit
  to the page shows the next set; set 1 is the six highlights. Each card has
  the drive time, distance, route type, difficulty and a QR code to the trail;
  the right column has a QR code to the whole list. Data is in the
  `weather_page1` lambda (`HIKES[]`, `SETS[][]`).
- **Snow depth:** the frame fetches Open-Meteo's modelled snow depth for the
  house every 3 hours (and on wake until it has one) and publishes it to HA as
  "Snow depth at house". HA's Scrape helper can't read JSON, hence on-device.
- **Santa's Village:** dates and hours come from the `santa_days` global
  (2026 Christmastime schedule from santasvillage.com). **Update it each fall.**
  QR codes: Christmastime tickets and the park calendar.
- **Testing:** `input_select.e_ink_page` (dashboard: "Page override") pins a
  page whether or not it's in season; `auto` resumes the rotation. While a
  page is pinned, Next page steps through its sets (the three hike sets).
- QR codes reuse one `qr_code` object (`qr_dyn`, set_value then draw), because
  each one holds a ~4 KB buffer in internal RAM.
- To add a page: bump `NUM_PAGES` and add its eligibility in both page tables
  (`weather_page1` lambda and the `next_page` script), the override names in
  both places plus the `page_override` text sensor, then its body block.
