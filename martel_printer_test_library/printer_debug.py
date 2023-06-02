from enum import Enum
import time
from typing import Final, Optional

from robot.api import FatalError, Failure
from robot.api.deco import keyword, library
from robot.libraries import Dialogs

from martel_printer import Printer
from martel_printer.command_set import debug_protocol as debug
from martel_printer.command_set.debug_protocol import MeasureChannel, SetChannel

from . import setup
from .setup import CommsProtocol
from .environment import TestEnvironment, Skip


class PrinterTest(Enum):
    BATTERY_VOLTAGE = MeasureChannel.BATTERY_VOLTAGE
    CHARGER_VOLTAGE = MeasureChannel.CHARGER_VOLTAGE
    VCC_VOLTAGE = MeasureChannel.VCC_VOLTAGE
    MECH_VOLTAGE = MeasureChannel.MECH_VOLTAGE

    MECH_TEMPERATURE = MeasureChannel.MECH_TEMPERATURE
    PAPER_SENSOR = MeasureChannel.PAPER_SENSOR
    WAKEUP_SIGNAL = MeasureChannel.WAKEUP_SIGNAL
    BUTTON_STATE = MeasureChannel.BUTTON_STATE
    RTC_PRESENT = MeasureChannel.RTC_PRESENT
    PRINTER_FIRMWARE_CHECKSUM = MeasureChannel.PRINTER_FIRMWARE_CHECKSUM
    MECH_BUSY = MeasureChannel.MECH_BUSY

    BLUETOOTH_ADDRESS_1 = MeasureChannel.BLUETOOTH_ADDRESS_1
    BLUETOOTH_ADDRESS_2 = MeasureChannel.BLUETOOTH_ADDRESS_2
    BLUETOOTH_ADDRESS_3 = MeasureChannel.BLUETOOTH_ADDRESS_3

    FONT_LIBRARY_VALID = MeasureChannel.FONT_LIBRARY_VALID

    ADC_PAPER_SENSOR = MeasureChannel.ADC_PAPER_SENSOR
    ADC_MECH_TEMPERATURE = MeasureChannel.ADC_MECH_TEMPERATURE
    ADC_BATTERY = MeasureChannel.ADC_BATTERY
    ADC_CHARGER = MeasureChannel.ADC_CHARGER

    FONT_LIBRARY_VERSION_MAJOR = MeasureChannel.FONT_LIBRARY_VERSION_MAJOR
    FONT_LIBRARY_VERSION_MINOR = MeasureChannel.FONT_LIBRARY_VERSION_MINOR
    BLUETOOTH_FIRMWARE_VERSION_MAJOR = MeasureChannel.BLUETOOTH_FIRMWARE_VERSION_MAJOR
    BLUETOOTH_FIRMWARE_VERSION_MINOR = MeasureChannel.BLUETOOTH_FIRMWARE_VERSION_MINOR


@library(scope="GLOBAL")
class PrinterDebugLibrary:
    def __init__(self, env: TestEnvironment = TestEnvironment()) -> None:
        self._printer: Optional[Printer] = None

        if env.debug_interface is None or isinstance(env.debug_interface, Skip):
            return

        self._printer = Printer(env.debug_interface)

    @keyword("Setup Printer Debug Library")
    def setup(self) -> None:
        if self._printer is not None:
            return

        # Ask the user which protocol to use for printer debug commands.
        # Then ask the user to setup an interface for the specified protocol.
        selection: str = Dialogs.get_selection_from_user(
            "Select a protocol for printer debug operations:",
            *[comms.name for comms in CommsProtocol],
        )
        protocol = next(i for i in CommsProtocol if i.name == selection)
        comms = setup.from_user_get_comms_interface(protocol, allow_skip=False)

        if comms is None:
            raise FatalError("Printer Debug library must have an interface.")

        self._printer = Printer(comms)

    @keyword("Printer Reset")
    def reset(self) -> None:
        if self._printer is None:
            raise FatalError("Printer debug port has not been set.")

        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.reset())
        time.sleep(1.5)

    @keyword("Printer Set Option")
    def set_option(self, option: int, setting: int) -> None:
        if self._printer is None:
            raise FatalError("Printer debug port has not been set.")

        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.set_option(option, setting))

    @keyword("Printer Print Selftest")
    def print_selftest(self) -> None:
        if self._printer is None:
            raise FatalError("Printer debug port has not been set.")

        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.set_channel(SetChannel.PRINT_SELFTEST))

    @keyword("Printer Redirect Enable")
    def redirect_enable(self) -> None:
        if self._printer is None:
            raise FatalError("Printer debug port has not been set.")

        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.set_channel(SetChannel.ENABLE_PRINT_REDIRECT))

    @keyword("Printer Redirect Disable")
    def redirect_disable(self) -> None:
        if self._printer is None:
            raise FatalError("Printer debug port has not been set.")

        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.set_channel(SetChannel.DISABLE_PRINT_REDIRECT))

    @keyword("Printer Power Off")
    def sleep(self) -> None:
        if self._printer is None:
            raise FatalError("Printer debug port has not been set.")

        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.set_channel(SetChannel.POWER_OFF))

    @keyword("Printer Measure")
    def printer_test_equal(self, channel: PrinterTest) -> int | float:
        if self._printer is None:
            raise FatalError("Printer debug port has not been set.")

        self._printer.send(debug.set_debug_mode())
        response: Final = self._printer.send_and_get_response(
            debug.measure_channel(channel.value), terminator=b"\r"
        )

        if not response.endswith(b"\r"):
            raise Failure(
                "Unexpected response from printer.\n"
                f"Response: [{response.hex(' ').upper()}]\n"
                "CR terminator not present. Response may be incomplete."
            )
        result = int(response.removesuffix(b"\r"), 16)

        if (
            channel == PrinterTest.BATTERY_VOLTAGE
            or channel == PrinterTest.CHARGER_VOLTAGE
            or channel == PrinterTest.VCC_VOLTAGE
            or channel == PrinterTest.MECH_VOLTAGE
            or channel == PrinterTest.MECH_TEMPERATURE
        ):
            return float(result) / 1000

        return result
