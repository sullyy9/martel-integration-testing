import logging
from enum import IntEnum, unique
from typing import Final

from .common import ControlCode as CC


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


@unique
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
    AUTO_POWER_ON = 19

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
    FONT_SLOT_HP_ALTERNATIVE = 66

    HARDWARE_NO_RS232 = 67
    HARDWARE_NO_USB = 68
    HARDWARE_NO_BT = 69
    HARDWARE_NO_IR = 70
    HARDWARE_NO_RTC = 71


@unique
class MeasureChannel(IntEnum):
    BATTERY_VOLTAGE = 0
    CHARGER_VOLTAGE = 1
    VCC_VOLTAGE = 2
    MECH_VOLTAGE = 3  # Just battery voltage
    MECH_TEMPERATURE = 4
    PAPER_SENSOR = 5
    WAKEUP_SIGNAL = 6
    BUTTON_STATE = 8
    UNUSED_1 = 9
    RTC_PRESENT = 10
    UNUSED_2 = 11
    PRINTER_FIRMWARE_CHECKSUM = 12
    MECH_BUSY = 13
    UNUSED_3 = 14
    UNUSED_4 = 15
    BLUETOOTH_ADDRESS_1 = 16
    BLUETOOTH_ADDRESS_2 = 17
    BLUETOOTH_ADDRESS_3 = 18

    FONT_LIBRARY_VALID = 19

    ADC_PAPER_SENSOR = 20
    ADC_MECH_TEMPERATURE = 21
    ADC_BATTERY = 22
    ADC_CHARGER = 23

    FONT_LIBRARY_VERSION_MAJOR = 26
    FONT_LIBRARY_VERSION_MINOR = 27
    BLUETOOTH_FIRMWARE_VERSION_MAJOR = 28
    BLUETOOTH_FIRMWARE_VERSION_MINOR = 29

    CONFIG_OPTION_1 = 32


class SetChannel(IntEnum):
    CHARGE_TEST = 0
    CTS_TEST = 1
    FEED_PAPER = 3
    SLEEP = 4
    POWER_OFF = 5
    ENABLE_PRINT_REDIRECT = 6
    DISABLE_PRINT_REDIRECT = 7
    PRINT_SELFTEST = 8


log: Final[logging.Logger] = logging.getLogger("debug protocol")


def set_debug_mode(mode: DebugMode = DebugMode.AUTOTEST) -> bytes:
    log.info(f"Sending set debug mode command with parameters [mode={mode}]")
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord("D"), mode])


def set_option(option: ConfigOption | int, setting: int) -> bytes:
    log.info(
        f"Sending enable debug command with parameters "
        f"[option={option}, setting={setting}]"
    )
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord("O"), option, setting])


def measure_option(option: ConfigOption | int) -> bytes:
    channel = (MeasureChannel.CONFIG_OPTION_1 - 1) + option

    log.info(f"Sending measure option command with parameters [option={option}]")
    return measure_channel(channel)


def reset() -> bytes:
    log.info(f"Sending reset command")
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord("@")])


def measure_channel(channel: MeasureChannel | int) -> bytes:
    log.info(f"Sending measure channel command with parameters " f"[channel={channel}]")
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord("M"), channel])


def set_channel(channel: SetChannel | int) -> bytes:
    log.info(f"Sending set channel command with parameters [channel={channel}]")
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord("S"), channel])


def set_name(name: str) -> bytes:
    if not name.endswith("\0"):
        name += "\0"

    log.info(f"Sending set name command with parameters [name={name}]")
    name_bytes: bytes = bytes(name.encode("ascii"))
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord("N")]) + name_bytes


def reset_timer() -> bytes:
    log.info(f"Sending reset timer command")
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord("R")])


def print_timer() -> bytes:
    log.info(f"Sending print timer command")
    return bytes([CC.ESC, CC.NULL, CC.NULL, ord("T")])
