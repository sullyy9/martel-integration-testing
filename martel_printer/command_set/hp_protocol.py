import logging
from typing import Final

from .common import ControlCode as CC


log: Final[logging.Logger] = logging.getLogger("HP protocol")


def enable_default_font() -> bytes:
    log.info("Enabling default font")
    return bytes([CC.ESC, 248])


def enable_alternative_font() -> bytes:
    log.info("Enabling alternative font")
    return bytes([CC.ESC, 249])
