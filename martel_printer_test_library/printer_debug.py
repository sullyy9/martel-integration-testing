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

    @keyword("Printer Firmware Checksum Should Be")
    def measure_printer_firmware_checksum(self, checksum: int) -> None:
        if self._printer is None:
            raise FatalError("Printer debug port has not been set.")

        self._printer.send(debug.set_debug_mode())
        command: Final = debug.measure_channel(MeasureChannel.PRINTER_FIRMWARE_CHECKSUM)
        response: Final = self._printer.send_and_get_response(
            command, terminator="\r".encode("ascii")
        )

        received_checksum: Final = int(response.removesuffix(b"\r"), 16)
        if checksum != received_checksum:
            raise Failure(
                "Printer firmware checksum does not match the expected value\n"
                f"Expected: {checksum}\n"
                f"Received: {received_checksum}"
            )
