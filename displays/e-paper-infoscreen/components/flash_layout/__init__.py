"""flash_layout: use the partition table in this folder instead of ESPHome's.

`esp32: partitions:` takes a file next to the device YAML; this keeps the
table in the repository with the display instead. A partition table only
changes with a USB (serial) flash; OTA updates keep whatever is on the chip.
"""

from pathlib import Path

from esphome.components.esp32 import add_extra_build_file
import esphome.config_validation as cv
from esphome.core import CORE

DEPENDENCIES = ["esp32"]
CODEOWNERS = ["@karlg100"]

CONF_TABLE = "table"
TABLES = {"inkplate10_4mb": "partitions_4mb.csv"}

CONFIG_SCHEMA = cv.Schema(
    {cv.Optional(CONF_TABLE, default="inkplate10_4mb"): cv.one_of(*TABLES, lower=True)}
)


async def to_code(config):
    path = Path(__file__).parent / TABLES[config[CONF_TABLE]]
    if not add_extra_build_file("partitions.csv", path):
        raise cv.Invalid("A partition table is already set (esp32: partitions:)")
    CORE.data.setdefault("flash_layout", {})["table"] = str(path)
