# ESPHome e-ink displays

ESPHome configurations and supporting assets for multiple e-ink displays.
Each display has its own directory and independently managed configuration.

## Layout

```text
displays/
  e-paper-infoscreen/
    e-paper-infoscreen.yaml
    secrets.example.yaml
    README.md
    fonts/
    images/
shared/
  README.md
```

| Display | Hardware | Configuration |
| --- | --- | --- |
| E-paper Infoscreen | Inkplate 10 / ESP32 | [e-paper-infoscreen.yaml](displays/e-paper-infoscreen/e-paper-infoscreen.yaml) |

Keep display-specific assets next to the YAML so its relative paths stay valid.
Move an asset or ESPHome package into `shared/` only when multiple displays
actually use it. Do not copy one device's identity or credentials to another.

## Local setup

For the chosen display, copy `secrets.example.yaml` to `secrets.yaml` in the same
directory and fill in the existing device credentials and Wi-Fi details.
Real secrets, build output, and local Home Assistant connection files are ignored.
The Home Assistant access token is not an ESPHome API encryption key.

With ESPHome installed, validate from the repository root:

```sh
esphome config displays/e-paper-infoscreen/e-paper-infoscreen.yaml
```

The infoscreen configuration with screenshot capture disabled was successfully
compiled on ESPHome 2026.9.0 on 2026-09-19. Google Fonts require network access;
commented-out external components are inactive. See the display README for build
results, dependencies, and known issues.

## Adding a display

1. Create `displays/<unique-device-name>/` with `<unique-device-name>.yaml`.
2. Give it a unique ESPHome node name and its own credentials.
3. Add its local assets, a `secrets.example.yaml`, and a README documenting
   hardware, Home Assistant dependencies, and deployment target.
4. Add it to the table above and validate that display independently.

## Live deployment scope

The current authorized live target is only:

```text
hassio@192.168.10.8:/root/config/esphome/e-paper-infoscreen.yaml
```

The remote directory contains other projects. Never synchronize this repository
over the entire remote directory, delete remote files, or overwrite shared
fonts, images, or secrets. This repository setup does not deploy or flash anything.

The repository YAML replaces embedded API and OTA credentials with named
`!secret` references. Before deployment, resolve those references using the
existing device credentials into a private deployment copy, or establish an
explicitly authorized secrets mapping. Do not upload unresolved new secret
references or modify the server's shared `secrets.yaml` under the current scope.
Keep a private backup of the live YAML before making a targeted change.
