# Repository instructions

- This repository supports multiple independent ESPHome e-ink displays.
- Put each display in `displays/<device-name>/`; keep its assets and documentation beside it.
- Use `shared/` only for assets or packages actually used by multiple displays.
- Never commit credentials, Home Assistant tokens, real secrets.yaml files, or raw live backups.
- The currently authorized remote write scope is ONLY `/root/config/esphome/e-paper-infoscreen.yaml` on `hassio@192.168.10.8`.
- Other remote ESPHome projects and shared files must not be edited, renamed, deleted, or overwritten.
- Read-only copies of assets referenced by the target display are allowed.
- Do not bulk-sync, deploy, restart, or flash devices as part of repository maintenance.
- Preserve existing API and OTA credentials during a future authorized deployment. Resolve repository secret references without modifying remote shared secrets under the current scope.
- Validate the affected display before proposing a firmware deployment; clearly report checks not run.
