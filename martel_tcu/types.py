from enum import IntEnum, unique
from typing import Final


@unique
class RelayChannel(IntEnum):
    BATTERY_CONNECT = 0x00  # Closes battery relay. Opens battery and Charger.
    BATTERY_VOLTAGE_SET_4V45 = 0x01
    CURRENT_MEASURE_ENABLE = 0x02

    CHARGER_CONNECT = 0x04  # Closes battery and charger relay. Opens Charger.
    CHARGER_VOLTAGE_LIMIT_5V = 0x1D
    CHARGER_VOLTAGE_LIMIT_8V = 0x05
    CHARGER_VOLTAGE_LIMIT_12V = 0x06
    CHARGER_VOLTAGE_LIMIT_17V = 0x07

    COMMS_MODE_BIT0 = 0x0C
    COMMS_MODE_BIT1 = 0x0D
    COMMS_MODE_BIT2 = 0x0E
    COMMS_MODE_BIT3 = 0x0F

    BAUD_RATE_BIT0 = 0x10
    BAUD_RATE_BIT1 = 0x11
    BAUD_RATE_BIT2 = 0x12
    BAUD_RATE_BIT3 = 0x1C

    PARITY_ENABLE = 0x13  # 0: None, 1: See PARITY_EVEN_ODD
    PARITY_SET_EVEN = 0x14  # 0: Odd, 1: Even

    PROTOCOL_BIT_0 = 0x18
    PROTOCOL_BIT_1 = 0x19

    DATA_BITS_SET_7 = 0x1A  # 0: 8 bits, 1: 7 bits
    PARITY_SET_SPACE_MARK = 0x1B

    BATTERY_ENABLE = 0x21
    BATTERY_VOLTAGE_SET = 0x20
    BATTERY_CURRENT_LIMIT_ENABLE = 0x22
    BATTERY_TRIP_DISABLE = 0x23

    CHARGER_ENABLE = 0x31
    CHARGER_VOLTAGE_SET = 0x30
    CHARGER_CURRENT_LIMIT_ENABLE = 0x32
    CHARGER_TRIP_DISABLE = 0x33

    COMMS_MODE_SET = 0x40
    BAUD_RATE_SET = 0x41


@unique
class MeasureChannel(IntEnum):
    BATTERY_CURRENT = 0x00
    CHARGER_CURRENT = 0x01
    CTS_LEVEL = 0x02

    BATTERY_VOLTAGE = 0x03
    BATTERY_VOLTAGE_DROP_100MS = 0x04
    BATTERY_VOLTAGE_DROP_500MS = 0x05
    BATTERY_VOLTAGE_DROP_2S = 0x06
    BATTERY_VOLTAGE_DROP_5S = 0x07

    TCU_FIRMWARE_VERSION = 0x08
    TCU_REFERENCE_VOLTAGE = 0x09
    TCU_INTERNAL_BATTERY_VOLTAGE = 0x0A
    TCU_INTERNAL_CHARGER_VOLTAGE = 0x0B

    BLUETOOTH_ADDRESS_UPPER = 0x10
    BLUETOOTH_ADDRESS_MIDDLE = 0x11
    BLUETOOTH_ADDRESS_LOWER = 0x12
    BLUETOOTH_ADDRESS_READY = 0x13
    BLUETOOTH_CONNECT_PIN_0 = 0x14
    BLUETOOTH_CONNECT_PIN_1234 = 0x15
    BLUETOOTH_CONNECT_PIN_4254 = 0x16


class CommsMode(IntEnum):
    """
    Communication protocols supported by the TCU for communicating with the
    printer. For use with the RelayChannel.COMMS_MODE channel.

    """

    RS232 = 0
    TTL = 1
    RS232_RX_IRDA_TX = 2
    TTL_RX_IRDA_TX = 3
    RS232_RX_HPIR_TX = 4
    TTL_RX_HPIR_TX = 5
    IRDA = 6
    RS232_RX_PARALLEL_TX = 7
    RS485 = 8
    BLUETOOTH = 9


BAUD_RATE_LUT: Final = [
    {9600: 0},
    {19200: 1},
    {300: 2},
    {600: 3},
    {1200: 4},
    {2400: 5},
    {4800: 6},
    {38400: 7},
    {58400: 8},
    {115200: 9},
    {9600: 10},
    {9600: 11},
    {9600: 12},
    {9600: 13},
    {9600: 14},
    {9600: 15},
]
