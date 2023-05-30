from enum import Enum, auto
from pathlib import Path
from typing import Optional
from functools import partial

from robot.api import Failure, FatalError, SkipExecution
from robot.api.deco import keyword, library
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

from martel_printer import Printer, Encoding
from martel_printer.comms import Parity
from martel_printer.command_set import martel_protocol as martel
from martel_printer.command_set import debug_protocol as debug

from . import setup
from .setup import CommsProtocol
from .environment import TestEnvironment, Skip


class TextSequence(Enum):
    FULL_CHARACTER_SET = auto()

    def get_sequence(self) -> bytes:
        match self:
            case self.FULL_CHARACTER_SET:
                data: bytes = bytes()
                for i in range(0, 256):
                    data += martel.print_character(i)
                    if i % 15 == 0:
                        data += bytes([ord("\n")])
                return data


class Command(Enum):
    ENABLE_BOLD_COMMAND = partial(martel.bold_enable)
    DISABLE_BOLD_COMMAND = partial(martel.bold_disable)

    ENABLE_ITALIC_COMMAND = partial(martel.italic_enable)
    DISABLE_ITALIC_COMMAND = partial(martel.italic_disable)

    def __call__(self, *args) -> bytes:
        return self.value(*args)


@library(scope="GLOBAL")
class PrinterTestLibrary:
    """

    TODO
    ----
        When Robot Frameworks allows mixing embedded and normal aruments,
        replace the variations of each keyword.
    """

    def __init__(self, env: TestEnvironment = TestEnvironment()) -> None:
        self._outdir: Optional[Path]

        self._secure_comms: Optional[Printer] = None
        self._comms: dict[CommsProtocol, Optional[Printer]] = {
            CommsProtocol.USB: None,
            CommsProtocol.RS232: None,
            CommsProtocol.IrDA: None,
            CommsProtocol.Bluetooth: None,
        }

        if env.usb_interface and not isinstance(env.usb_interface, Skip):
            self._comms[CommsProtocol.USB] = Printer(env.usb_interface)

        if env.rs232_interface and not isinstance(env.rs232_interface, Skip):
            self._comms[CommsProtocol.RS232] = Printer(env.rs232_interface)

        if env.infrared_interface and not isinstance(env.infrared_interface, Skip):
            self._comms[CommsProtocol.IrDA] = Printer(env.infrared_interface)

        if env.bluetooth_interface and not isinstance(env.bluetooth_interface, Skip):
            self._comms[CommsProtocol.Bluetooth] = Printer(env.bluetooth_interface)

    @keyword("Setup Printer Test Library")
    def setup(self) -> None:
        for interface in CommsProtocol:
            if self._comms[interface] is None:
                comms = setup.from_user_get_comms_interface(interface)
                self._comms[interface] = Printer(comms) if comms else None

    ############################################################################

    @keyword("USB Configure")
    def usb_configure(
        self,
        baud_rate: Optional[int] = None,
        data_bits: Optional[int] = None,
        parity: Optional[Parity] = None,
    ) -> None:
        self.configure_comms(CommsProtocol.USB, baud_rate, data_bits, parity)

    @keyword("RS232 Configure")
    def rs232_configure(
        self,
        baud_rate: Optional[int] = None,
        data_bits: Optional[int] = None,
        parity: Optional[Parity] = None,
    ) -> None:
        self.configure_comms(CommsProtocol.RS232, baud_rate, data_bits, parity)

    @keyword("IrDA Configure")
    def irda_configure(
        self,
        baud_rate: Optional[int] = None,
        data_bits: Optional[int] = None,
        parity: Optional[Parity] = None,
    ) -> None:
        self.configure_comms(CommsProtocol.IrDA, baud_rate, data_bits, parity)

    @keyword("Bluetooth Configure")
    def bt_configure(
        self,
        baud_rate: Optional[int] = None,
        data_bits: Optional[int] = None,
        parity: Optional[Parity] = None,
    ) -> None:
        self.configure_comms(CommsProtocol.Bluetooth, baud_rate, data_bits, parity)

    def configure_comms(
        self,
        interface: CommsProtocol,
        baud_rate: Optional[int] = None,
        data_bits: Optional[int] = None,
        parity: Optional[Parity] = None,
    ) -> None:
        """
        Configure the given interface.

        Parameters
        ----------
        interface : CommsProtocol
            The communications interface.

        baud_rate : int
            baud rate to set.

        data_bits : int
            Data bits to set.

        parity : Parity
            Parity to set.

        Raises
        ------
        SkipExecution
            If the given interface has not been configured.

        """
        comm_interface = self._comms[interface]
        if not comm_interface:
            raise SkipExecution(f"Skipping tests requiring {interface} interface.")

        if baud_rate is not None:
            comm_interface.comms.baudrate = baud_rate
        if data_bits is not None:
            comm_interface.comms.bytesize = data_bits
        if parity is not None:
            comm_interface.comms.parity = parity

    ############################################################################

    @keyword("USB Print")
    def usb_print(self, text: str, encoding: Encoding = Encoding.ASCII) -> None:
        self.print(CommsProtocol.USB, text, encoding)

    @keyword("RS232 Print")
    def rs232_print(self, text: str, encoding: Encoding = Encoding.ASCII) -> None:
        self.print(CommsProtocol.RS232, text, encoding)

    @keyword("IrDA Print")
    def irda_print(self, text: str, encoding: Encoding = Encoding.ASCII) -> None:
        self.print(CommsProtocol.IrDA, text, encoding)

    @keyword("Bluetooth Print")
    def bt_print(self, text: str, encoding: Encoding = Encoding.ASCII) -> None:
        self.print(CommsProtocol.Bluetooth, text, encoding)

    def print(
        self, interface: CommsProtocol, text: str, encoding: Encoding = Encoding.ASCII
    ) -> None:
        """
        Print a string using the given comms interface and capture the printout
        using the selected mech analyzer.

        Parameters
        ----------
        text : str
            Text string to be printed.

        interface : CommsInterface
            Specifies the comms interface that should be used to transmit the
            text to the printer.

        Raises
        ------
        SkipExecution
            If the comms interface or a mech analyser has not been set.

        """
        comm_interface = self._comms[interface]
        if not comm_interface:
            raise SkipExecution(f"Skipping tests requiring {interface} interface.")

        comm_interface.print(text, encoding=encoding)

    ############################################################################

    @keyword("USB Print Sequence")
    def usb_print_sequence(
        self, text: TextSequence, encoding: Encoding = Encoding.ASCII
    ) -> None:
        self.print_sequence(CommsProtocol.USB, text, encoding)

    @keyword("RS232 Print Sequence")
    def rs232_print_sequence(
        self, text: TextSequence, encoding: Encoding = Encoding.ASCII
    ) -> None:
        self.print_sequence(CommsProtocol.RS232, text, encoding)

    @keyword("IrDA Print Sequence")
    def irda_print_sequence(
        self, text: TextSequence, encoding: Encoding = Encoding.ASCII
    ) -> None:
        self.print_sequence(CommsProtocol.IrDA, text, encoding)

    @keyword("Bluetooth Print Sequence")
    def bt_print_sequence(
        self, text: TextSequence, encoding: Encoding = Encoding.ASCII
    ) -> None:
        self.print_sequence(CommsProtocol.Bluetooth, text, encoding)

    def print_sequence(
        self,
        interface: CommsProtocol,
        text: TextSequence,
        encoding: Encoding = Encoding.ASCII,
    ) -> None:
        """
        Print a string using the given comms interface and capture the printout
        using the selected mech analyzer.

        Parameters
        ----------
        text : str
            Text string to be printed.

        interface : CommsInterface
            Specifies the comms interface that should be used to transmit the
            text to the printer.

        Raises
        ------
        SkipExecution
            If the comms interface or a mech analyser has not been set.

        """
        comm_interface = self._comms[interface]
        if not comm_interface:
            raise SkipExecution(f"Skipping tests requiring {interface} interface.")

        comm_interface.send(text.get_sequence())
        comm_interface.println()

    ############################################################################

    @keyword("USB Send")
    def usb_send(self, data: bytes) -> None:
        self.send(CommsProtocol.USB, data)

    @keyword("RS232 Send")
    def rs232_send(self, data: bytes) -> None:
        self.send(CommsProtocol.RS232, data)

    @keyword("IrDA Send")
    def irda_send(self, data: bytes) -> None:
        self.send(CommsProtocol.IrDA, data)

    @keyword("Bluetooth Send")
    def bt_send(self, data: bytes) -> None:
        self.send(CommsProtocol.Bluetooth, data)

    def send(self, interface: CommsProtocol, data: bytes) -> None:
        comm_interface = self._comms[interface]
        if not comm_interface:
            raise SkipExecution(f"Skipping tests requiring {interface} interface.")

        comm_interface.send(data)

    ############################################################################

    @keyword("USB Send Command")
    def usb_send_command(self, command: Command) -> None:
        self.send_command(CommsProtocol.USB, command)

    @keyword("RS232 Send Command")
    def rs232_send_command(self, command: Command) -> None:
        self.send_command(CommsProtocol.RS232, command)

    @keyword("IrDA Send Command")
    def irda_send_command(self, command: Command) -> None:
        self.send_command(CommsProtocol.IrDA, command)

    @keyword("Bluetooth Send Command")
    def bt_send_command(self, command: Command) -> None:
        self.send_command(CommsProtocol.Bluetooth, command)

    def send_command(self, interface: CommsProtocol, command: Command) -> None:
        comm_interface = self._comms[interface]
        if not comm_interface:
            raise SkipExecution(f"Skipping tests requiring {interface} interface.")

        comm_interface.send(command())

    ############################################################################

    @keyword("USB Send And Expect Echo")
    def usb_send_and_expect_echo(self, data: str) -> None:
        self.send_and_expect_echo(CommsProtocol.USB, data)

    @keyword("RS232 Send And Expect Echo")
    def rs232_send_and_expect_echo(self, data: str) -> None:
        self.send_and_expect_echo(CommsProtocol.RS232, data)

    @keyword("IrDA Send And Expect Echo")
    def irda_send_and_expect_echo(self, data: str) -> None:
        self.send_and_expect_echo(CommsProtocol.IrDA, data)

    @keyword("Bluetooth Send And Expect Echo")
    def bt_send_and_expect_echo(self, data: str) -> None:
        self.send_and_expect_echo(CommsProtocol.Bluetooth, data)

    def send_and_expect_echo(self, interface: CommsProtocol, data: str) -> None:
        comm_interface = self._comms[interface]
        if not comm_interface:
            raise SkipExecution(f"Skipping tests requiring {interface} interface.")

        response = comm_interface.send_and_get_response(
            data.encode("ascii"), timeout=5, terminator=data.encode("ascii")
        ).decode("ascii")

        if response != data:
            raise Failure(
                "Echo does not match the transmitted string\n"
                f"Expected: {data}\n"
                f"Response: {response}"
            )

    ############################################################################

    @keyword("USB Send Dummy Command And Expect Response")
    def usb_comms_check(self) -> None:
        self.comms_check(CommsProtocol.USB)

    @keyword("RS232 Send Dummy Command And Expect Response")
    def rs232_comms_check(self) -> None:
        self.comms_check(CommsProtocol.RS232)

    @keyword("IrDA Send Dummy Command And Expect Response")
    def irda_comms_check(self) -> None:
        self.comms_check(CommsProtocol.IrDA)

    @keyword("Bluetooth Dummy Send Command And Expect Response")
    def bt_comms_check(self) -> None:
        self.comms_check(CommsProtocol.Bluetooth)

    def comms_check(self, interface: CommsProtocol) -> None:
        comm_interface = self._comms[interface]
        if not comm_interface:
            raise SkipExecution(f"Skipping tests requiring {interface} interface.")

        response = comm_interface.send_and_get_response(
            debug.measure_channel(0), timeout=2, terminator=b"\r"
        ).decode("cp437")

        if response is None:
            raise Failure("Printer did not respond to comms check command")

    ############################################################################

    @keyword("Printer Clear Print Buffer")
    def clear_print_buffer(self) -> None:
        if self._secure_comms is None:
            raise FatalError("Secure printer comms has not been set.")

        self._secure_comms.send(martel.clear_print_buffer())

    def _get_test_name_or_none(self) -> str | None:
        """
        Return the test name if Robot Framework is running or none if it isn't.

        Returns
        -------
        str | None
            The test name if Robot Framework is running.
        """
        try:
            return BuiltIn().get_variable_value("${TEST NAME}")
        except RobotNotRunningError:
            return None
