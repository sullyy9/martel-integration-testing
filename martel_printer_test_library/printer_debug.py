import time

from robot.api import FatalError, Failure
from robot.api.deco import keyword, library
from robot.libraries import Dialogs

from martel_printer import Printer
from martel_printer.command_set import debug_protocol as debug
from martel_printer.command_set.debug_protocol import MeasureChannel, SetChannel

from . import setup
from .setup import CommsProtocol


@library(scope="GLOBAL")
class PrinterDebugLibrary:
    def __init__(self) -> None:
        self._printer: Printer

    @keyword("Setup Printer Debug Library")
    def setup(self) -> None:
        # Ask the user which protocol to use for printer debug commands.
        # Then ask the user to setup an interface for the specified protocol.
        selection: str = Dialogs.get_selection_from_user(
            f"Select a protocol for printer debug operations:",
            *[comms.name for comms in CommsProtocol],
        )
        protocol = next(i for i in CommsProtocol if i.name == selection)
        comms = setup.from_user_get_comms_interface(protocol, allow_skip=False)

        if comms is None:
            raise FatalError("Printer Debug library must have an interface.")

        self._printer = Printer(comms)

    @keyword("Printer Reset")
    def reset(self) -> None:
        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.reset())
        time.sleep(1.5)

    @keyword("Printer Set Option")
    def set_option(self, option: int, setting: int) -> None:
        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.set_option(option, setting))

    @keyword("Printer Print Selftest")
    def print_selftest(self) -> None:
        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.set_channel(SetChannel.PRINT_SELFTEST))

    @keyword("Printer Redirect Enable")
    def redirect_enable(self) -> None:
        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.set_channel(SetChannel.ENABLE_PRINT_REDIRECT))

    @keyword("Printer Redirect Disable")
    def redirect_disable(self) -> None:
        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.set_channel(SetChannel.DISABLE_PRINT_REDIRECT))

    @keyword("Printer Power Off")
    def sleep(self) -> None:
        self._printer.send(debug.set_debug_mode())
        self._printer.send(debug.set_channel(SetChannel.POWER_OFF))

    @keyword('Printer Measure "${channel}"')
    def measure_battery_voltage(self, channel: MeasureChannel) -> float:
        raise NotImplementedError
