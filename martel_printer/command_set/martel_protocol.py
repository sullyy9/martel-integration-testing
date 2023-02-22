import logging
from enum import IntEnum, unique
from typing import Final

from .common import ControlCode as CC


@unique
class Barcode(IntEnum):
    UPC_A = 0
    UPC_E = 1
    EAN_13 = 2
    EAN_8 = 3
    CODE_39 = 4
    INTERLEAVED_2_OF_5 = 5
    CODABAR = 6
    CODE_128 = 7


log: Final[logging.Logger] = logging.getLogger('martel protocol')


def double_width_enable() -> bytes:
    log.info('Sending enable double width command')
    return bytes([CC.SO])


def double_width_disable() -> bytes:
    log.info('Sending disable double width command')
    return bytes([CC.SI])


def clear_print_buffer() -> bytes:
    log.info('Sending print buffer command')
    return bytes([CC.CAN])


def set_print_mode(font: int,
                   double_height: bool = False,
                   double_width: bool = False
                   ) -> bytes:

    if not 0 <= font <= 3:
        message = (
            f'Invalid font value [font={font}] to print mode command. '
            f'Value must be 0 <= and <= 3.'
        )
        log.error(message)
        raise ValueError(message)

    word = font
    word += 0x10 if double_height else 0
    word += 0x20 if double_width else 0

    log.info(
        f'Sending print mode command with parameters [font={font}, '
        f'double_height={double_height}, double_width={double_width}]'
    )
    return bytes([CC.ESC, ord('!'), word])


def set_underline_mode(enabled: bool) -> bytes:
    log.info(
        f'Sending set underline mode command with parameters '
        f'[enabled={enabled}]'
    )
    enable_byte = 1 if enabled else 0
    return bytes([CC.ESC, ord('_'), enable_byte])


def set_print_defaults() -> bytes:
    log.info(f'Sending set print defaults command')
    return bytes([CC.ESC, ord('@')])


def bold_enable() -> bytes:
    log.info(f'Sending enable bold command')
    return bytes([CC.ESC, ord('G')])


def bold_disable() -> bytes:
    log.info(f'Sending disable bold command')
    return bytes([CC.ESC, ord('H')])


def set_encoding(font: int) -> bytes:
    if not 1 <= font <= 8:
        message = (
            f'Invalid font value [font={font}] to set encoding command. '
            f'Value must be 1 <= and <= 8.'
        )
        log.error(message)
        raise ValueError(message)

    log.info(f'Sending set encoding command with parameters [font={font}]')
    return bytes([CC.ESC, ord('e'), font])


def print_character(code_point: int) -> bytes:
    log.info(
        f'Sending print character command with parameters '
        f'[code_point={code_point}]'
    )
    return bytes([CC.ESC, ord('6'), code_point])


def set_barcode_magnification(magnification: int) -> bytes:
    if not 2 <= magnification <= 4:
        message = (
            f'Invalid font value [magnification={magnification}] to set '
            f'encoding command. Value must be 2 <= and <= 4.'
        )
        log.error(message)
        raise ValueError(message)

    log.info(
        f'Sending set barcode magnification command with parameters '
        f'[magnification={magnification}].'
    )

    return bytes([CC.GS, ord('w'), magnification])


def print_barcode(barcode: Barcode, data: str) -> bytes:
    log.info(
        f'Sending print barcode command with parameters '
        f'[barcode={barcode}, data={data}].'
    )

    return bytes([CC.GS, ord('k'), barcode]) + data.encode('ascii')


def italic_enable() -> bytes:
    log.info(f'Sending enable italic command')
    return bytes([CC.ESC, ord('4')])


def italic_disable() -> bytes:
    log.info(f'Sending disable italic command')
    return bytes([CC.ESC, ord('5')])
