"""web_image: an `image:` platform for pictures that live on someone else's web site.

The file is downloaded once into the ESPHome data directory and reused by every
later build (no network call while the file is there), then cropped, toned and
dithered to 1-bit for the e-paper panel at compile time. Nothing is committed to
the repository: delete `.esphome/web_image/` (or change the URL) to fetch again.
"""

CODEOWNERS = ["@karlg100"]
