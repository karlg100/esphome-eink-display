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

## Known issues to investigate

The initial Home Assistant state check found 44 distinct referenced entity IDs,
11 absent from current states and four with `unknown` values. These are a point-in-time
observation, not proof that the missing entities were deleted from the registry.

The numeric `hottub_setpoint` sensor reads `hvac_action`; the intended target
setpoint is the thermostat's `temperature` attribute. Daily condition entities,
some former forecast entities, visibility, wind gusts, and the generated forecast
also need review. These data issues have not been changed by disabling screenshot capture.

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
