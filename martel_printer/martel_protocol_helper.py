import os
import logging
from typing import Final

from .common_types import ControlCode as CC

log: Final[logging.Logger] = logging.getLogger('martel protocol')


class MartelProtocolError(Exception):
    ...


def clear_print_buffer_command() -> bytes:
    log.info('Creating clear print buffer command')
    return bytes([CC.CAN])


def print_mode_command(font: int, double_height: bool = False, double_width: bool = False) -> bytes:
    log.info(f'Creating print mode command with parameters [font={font}, ' +
             f'double_height={double_height}, double_width={double_width}]')

    if not 0 <= font <= 3:
        raise MartelProtocolError from ValueError(
            f'Invalid font value ({font}) to print mode command helper.',
            f'{os.linesep}',
            f'Value must be >= 0 and <= 3'
        )

    word = font
    word = word + 0x10 if double_height else word
    word = word + 0x20 if double_width else word
    return bytes([CC.ESC, ord('!'), word])

def set_encoding_command(font: int) -> bytes:
    log.info(f'Creating set encoding command with parameter font={font}')

    if not 1 <= font <= 8:
        raise MartelProtocolError from ValueError(
            f'Invalid font value ({font}) to set encoding command helper.',
            f'{os.linesep}',
            f'Value must be >= 1 and <= 8'
        )

    return bytes([CC.ESC, ord('e'), font])