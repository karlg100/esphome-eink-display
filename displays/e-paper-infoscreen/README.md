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
