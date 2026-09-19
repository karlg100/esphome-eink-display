# Display images pending import

The live YAML references these existing files under `/root/config/esphome/images/`:

- `ss-white-cropped.png`
- `ss-black-cropped.png`
- `ss-black-on-white-large.png`

The SSH connection became unreachable after the font was copied during the initial
import. These three image files have not been copied into this repository yet.
Copy only these files from the server into this directory when access returns;
do not modify or synchronize the remote image directory. A local ESPHome build
requires these files in addition to local secrets and the external dependencies.
