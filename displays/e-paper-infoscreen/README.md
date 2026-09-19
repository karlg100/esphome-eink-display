# E-paper Infoscreen

Inkplate 10 using ESP32, ESP-IDF, 16 MB flash, a PCF85063 RTC, and Home Assistant
sensor imports. The initial configuration was read from
`/root/config/esphome/e-paper-infoscreen.yaml` on 2026-09-19 and matched the
user-provided source. Runtime logic is unchanged in this baseline.

## Included dependencies

- `fonts/materialdesignicons-webfont.ttf`: existing live Material Design Icons font.
- Three images in `images/`, copied from the exact files referenced by the live YAML.
- Inter fonts are fetched through ESPHome's `gfonts://` references.
- The external `display_capture` component uses
  `https://github.com/karlg100/esphome-display-screenshot`, branch `inkplate-support`.
  That branch is mutable; this baseline preserves the existing reference.
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
also need review. No fixes have been applied in the baseline commit.

## Deployment

Only the live `e-paper-infoscreen.yaml` is within the current remote write scope.
Fonts and images were copied locally. Their live counterparts must not be changed. See the repository README for handling secret references and keeping
other ESPHome projects untouched.
