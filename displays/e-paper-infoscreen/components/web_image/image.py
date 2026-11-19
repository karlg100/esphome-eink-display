"""`image: - platform: web_image` (see __init__.py)."""

from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

import esphome.codegen as cg
from esphome.components.image import (
    Image_,
    add_metadata,
    get_image_type_enum,
    get_transparency_enum,
)
import esphome.config_validation as cv
from esphome.const import CONF_DITHER, CONF_ID, CONF_RAW_DATA_ID, CONF_RESIZE, CONF_URL
from esphome.core import CORE, HexInt

_LOGGER = logging.getLogger(__name__)

CONF_CROP = "crop"
CONF_GAMMA = "gamma"
CONF_AUTOCONTRAST = "autocontrast"
CONF_SHARPEN = "sharpen"
CONF_THRESHOLD = "threshold"
CONF_ALPHA_AS_INK = "alpha_as_ink"
CONF_INVERT = "invert"
CONF_CACHED_PATH = "cached_path"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0 Safari/537.36"
)


def cache_dir() -> Path:
    return Path(CORE.data_dir) / "web_image"


def cache_path(url: str) -> Path:
    name = url.split("?")[0].rstrip("/").rsplit("/", 1)[-1]
    suffix = Path(name).suffix.lower() or ".img"
    digest = hashlib.sha256(url.encode()).hexdigest()[:16]
    return cache_dir() / f"{digest}{suffix}"


def is_svg(path: Path) -> bool:
    with path.open("rb") as f:
        return b"<svg" in f.read(2048)


def fetch(url: str) -> Path:
    """Return the cached copy of url, downloading it only if it is not there yet."""
    path = cache_path(url)
    if path.is_file() and path.stat().st_size > 0:
        _LOGGER.debug("web_image: reusing %s for %s", path, url)
        return path
    import requests

    _LOGGER.info("web_image: downloading %s", url)
    try:
        resp = requests.get(url, timeout=60, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise cv.Invalid(f"Could not download {url}: {exc}") from exc
    data = resp.content
    if b"<svg" not in data[:2048]:
        try:
            Image.open(io.BytesIO(data)).verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise cv.Invalid(f"{url} is not an image: {exc}") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_bytes(data)
    tmp.replace(path)
    return path


def _download(config):
    config[CONF_CACHED_PATH] = str(fetch(config[CONF_URL]))
    return config


def _crop(value):
    value = cv.ensure_list(cv.percentage)(value)
    if len(value) != 4 or not (value[0] < value[2] and value[1] < value[3]):
        raise cv.Invalid("crop is [left, top, right, bottom] as fractions, left < right, top < bottom")
    return value


CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.Required(CONF_ID): cv.declare_id(Image_),
            cv.Required(CONF_URL): cv.url,
            cv.Required(CONF_RESIZE): cv.dimensions,
            cv.Optional(CONF_CROP): _crop,
            # alpha channel is the ink (white-on-transparent logos)
            cv.Optional(CONF_ALPHA_AS_INK, default=False): cv.boolean,
            cv.Optional(CONF_INVERT, default=False): cv.boolean,
            # percent of the histogram clipped at each end, 0 = off
            cv.Optional(CONF_AUTOCONTRAST, default=0): cv.float_range(min=0, max=20),
            # < 1 lightens the mid tones (snow stays white, trails stay dark)
            cv.Optional(CONF_GAMMA, default=1.0): cv.float_range(min=0.1, max=4),
            cv.Optional(CONF_SHARPEN, default=False): cv.boolean,
            cv.Optional(CONF_DITHER, default="NONE"): cv.one_of(
                "NONE", "ATKINSON", "FLOYDSTEINBERG", upper=True
            ),
            cv.Optional(CONF_THRESHOLD, default=128): cv.int_range(min=1, max=254),
            cv.GenerateID(CONF_RAW_DATA_ID): cv.declare_id(cg.uint8),
        }
    ),
    _download,
)


def _load(path: Path, box: tuple[int, int]) -> Image.Image:
    if is_svg(path):
        import resvg_py

        # rasterize big, then scale down like any other picture
        data = resvg_py.svg_to_bytes(svg_path=str(path), width=box[0] * 4)
        return Image.open(io.BytesIO(bytes(data)))
    return Image.open(path)


def _atkinson(gray: Image.Image, threshold: int) -> Image.Image:
    w, h = gray.size
    px = [float(v) for v in gray.getdata()]
    out = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            i = row + x
            old = px[i]
            new = 255 if old >= threshold else 0
            out[i] = new
            err = (old - new) / 8.0
            if err == 0:
                continue
            if x + 1 < w:
                px[i + 1] += err
            if x + 2 < w:
                px[i + 2] += err
            if y + 1 < h:
                j = i + w
                if x > 0:
                    px[j - 1] += err
                px[j] += err
                if x + 1 < w:
                    px[j + 1] += err
            if y + 2 < h:
                px[i + 2 * w] += err
    return Image.frombytes("L", (w, h), bytes(out)).convert("1", dither=Image.Dither.NONE)


def render(path: Path, config) -> Image.Image:
    """The 1-bit picture (white = 1) for a config entry."""
    box = config[CONF_RESIZE]
    im = _load(path, box)
    if crop := config.get(CONF_CROP):
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    im = im.convert("RGBA")
    if config[CONF_ALPHA_AS_INK]:
        # ink wherever the logo is drawn, whatever its colour
        alpha = im.split()[-1]
        gray = ImageOps.invert(alpha)
    else:
        flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
        flat.alpha_composite(im)
        gray = flat.convert("L")
    gray.thumbnail(box, Image.Resampling.LANCZOS)
    if config[CONF_INVERT]:
        gray = ImageOps.invert(gray)
    if config[CONF_AUTOCONTRAST]:
        gray = ImageOps.autocontrast(gray, cutoff=config[CONF_AUTOCONTRAST])
    if config[CONF_GAMMA] != 1.0:
        g = config[CONF_GAMMA]
        gray = gray.point([round(255 * ((v / 255) ** g)) for v in range(256)])
    if config[CONF_SHARPEN]:
        gray = gray.filter(ImageFilter.UnsharpMask(radius=1.5, percent=160, threshold=3))
    dither = config[CONF_DITHER]
    if dither == "ATKINSON":
        return _atkinson(gray, config[CONF_THRESHOLD])
    if dither == "FLOYDSTEINBERG":
        return gray.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    t = config[CONF_THRESHOLD]
    return gray.point(lambda v: 255 if v >= t else 0).convert("1", dither=Image.Dither.NONE)


def encode_binary(im: Image.Image) -> list[int]:
    """Rows padded to bytes, MSB first, bit set = white (as the file platform)."""
    w, h = im.size
    stride = (w + 7) // 8
    data = [0] * (stride * h)
    px = im.load()
    for y in range(h):
        for x in range(w):
            if px[x, y]:
                data[y * stride + x // 8] |= 0x80 >> (x % 8)
    return data


async def to_code(config) -> None:
    im = render(Path(config[CONF_CACHED_PATH]), config)
    width, height = im.size
    prog_arr = cg.progmem_array(config[CONF_RAW_DATA_ID], [HexInt(b) for b in encode_binary(im)])
    cg.new_Pvariable(
        config[CONF_ID],
        prog_arr,
        width,
        height,
        get_image_type_enum("BINARY"),
        get_transparency_enum("opaque"),
    )
    add_metadata(config[CONF_ID], width, height, "BINARY", "opaque")
