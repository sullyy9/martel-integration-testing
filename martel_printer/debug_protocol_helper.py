from enum import IntEnum, unique

from .common_types import ControlCode as CC


class DebugProtocolError(Exception):
    ...


@unique
class DebugMode(IntEnum):
    AUTOTEST = 0
    MAIN_STATE = 1
    CHARGER = 2
    VOLTAGES = 3
    HEX_DUMP = 4
    STACK = 5
    DATETIME = 6
    OPTIONS = 7
    PROTOCOL = 8


class ConfigOption(IntEnum):
    DATA_BITS_PARITY_1 = 1
    BAUD_RATE_1 = 2
    HANDSHAKE_1 = 3
    BLUETOOTH_PAIRING = 4
    DEFAULT_FONT = 5
    DOUBLE_WIDTH_HEIGHT = 6
    DENSITY = 7
    CURRENT = 8
    LABEL_UPSIDE = 9
    SLEEP_TIME = 10
    ESCAPE_MODE = 11
    TIME_FORMAT = 12
    USB_MODE = 13
    FAST_CHARGE = 14
    DATA_BITS_PARITY_2 = 15
    BAUD_RATE_2 = 16
    HANDSHAKE_2 = 17
    PROFILE = 18

    FONT_SLOT_DEFAULT_1 = 50
    FONT_SLOT_DEFAULT_2 = 51
    FONT_SLOT_DEFAULT_3 = 52
    FONT_SLOT_DEFAULT_4 = 53
    FONT_SLOT_DEFAULT_5 = 54
    FONT_SLOT_DEFAULT_6 = 55
    FONT_SLOT_DEFAULT_7 = 56
    FONT_SLOT_DEFAULT_8 = 57
    FONT_SLOT_ESC_0 = 58
    FONT_SLOT_ESC_1 = 59
    FONT_SLOT_ESC_2 = 60
    FONT_SLOT_ESC_3 = 61
    FONT_SLOT_ENCODING_1 = 62
    FONT_SLOT_ENCODING_2 = 63
    FONT_SLOT_ENCODING_3 = 64
    FONT_SLOT_ENCODING_4 = 65


class MeasureChannel(IntEnum):
    BATTERY_VOLTAGE = 1
    CHARGER_VOLTAGE = 2
    VCC_VOLTAGE = 3
    MECH_VOLTAGE = 4
    MECH_TEMPERATURE = 5
    PAPER_SENSOR = 6
    WAKEUP_SIGNAL = 7
    BUTTON_STATE = 8
    UNUSED_1 = 9
    RTC_PRESENT = 10
    UNUSED_2 = 11
    CHECKSUM = 12
    MECH_BUSY = 13
    UNUSED_3 = 14
    UNUSED_4 = 15
    BLUETOOTH_ADDRESS_1 = 16
    BLUETOOTH_ADDRESS_2 = 17
    BLUETOOTH_ADDRESS_3 = 18
    FONT_LIBRARY_VALID = 19
    CONFIG_OPTION_1 = 32


def enable_debug_command(mode: DebugMode = DebugMode.AUTOTEST) -> bytes:
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord('D'), mode])


def set_option_command(option: ConfigOption | int, setting: int) -> bytes:
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord('O'), option, setting])


def measure_option_command(option: ConfigOption | int) -> bytes:
    channel = (MeasureChannel.CONFIG_OPTION_1 - 1) + option
    return measure_command(channel)


def reset_command() -> bytes:
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord('@')])


def measure_command(channel: MeasureChannel | int) -> bytes:
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord('M'), channel])
