import os
from enum import StrEnum, auto, unique
from pathlib import Path
from typing import Optional, Self

from serial.tools.list_ports_common import ListPortInfo

from robot.api import Error, FatalError, ContinuableFailure
from robot.api.deco import keyword, library
from robot.libraries import Dialogs
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

import comms
from mech import PrintMechAnalyzer, LTPD245Emulator, EyeballMk1
from printout import Printout
from comms import (BaseCommsInterface, SerialCommsInterface, USBInterface,
                   RS232AdapterInterface, RS232TCUInterface,
                   IRAdapterInterface, IRTCUInterface)


PRINTER_VID = 0x483
PRINTER_PID = [0x1, 0x5740]

NULL = 0
ESC = 0x1B
CAN = 0x18

ENABLE_DEBUG = bytearray([ESC, NULL, NULL, ord('D'), NULL])
DEBUG_PRINT_SELFTEST = bytearray([ESC, NULL, NULL, ord('S'), 8])
DEBUG_SET_OPTION = bytearray([ESC, NULL, NULL, ord('O')])

COMMAND_RESET = bytearray([ESC, NULL, ord('@')])
COMMAND_CLEAR_PRINT_BUFFER = bytearray([CAN])


@unique
class CommsInterface(StrEnum):
    USB = auto()
    RS232 = auto()
    IR = auto()
    BLUETOOTH = auto()


@unique
class HardwareInterface(StrEnum):
    USB_ADAPTER = 'USB Adapter'
    TCU = 'TCU'

    @classmethod
    def from_user(cls, interface: str) -> Self:
        selection = Dialogs.get_selection_from_user(
            f'Select the printers {interface} hardware interface:',
            *[interface for interface in HardwareInterface]
        )
        return HardwareInterface(selection)

    def get_valid_ports(self) -> list[ListPortInfo]:
        match self:
            case HardwareInterface.USB_ADAPTER:
                return RS232AdapterInterface.get_valid_ports()
            case HardwareInterface.TCU:
                return RS232TCUInterface.get_valid_ports()

    def get_rs232_interface(self, port_name: str) -> SerialCommsInterface:
        match self:
            case HardwareInterface.USB_ADAPTER:
                return RS232AdapterInterface(port_name)
            case HardwareInterface.TCU:
                return RS232TCUInterface(port_name)

    def get_infrared_interface(self, port_name: str) -> SerialCommsInterface:
        match self:
            case HardwareInterface.USB_ADAPTER:
                return IRAdapterInterface(port_name)
            case HardwareInterface.TCU:
                return IRTCUInterface(port_name)


@unique
class PrintMechanism(StrEnum):
    EYEBALLMK1 = 'Eyeball Mk1'
    LTPD245EMULATOR = 'LTPD245 Emulator'


@unique
class FrameFormat(StrEnum):
    NONE_8BITS = '8 Bits None',
    EVEN_8BITS = '8 Bits Even',
    ODD_8BITS = '8 Bits Odd',
    EVEN_7BITS = '7 Bits Even',
    ODD_7BITS = '7 Bits Odd'


def get_serial_port_from_user(interface: str, port_list: list[ListPortInfo]) -> str:
    selected_port = Dialogs.get_selection_from_user(
        f'Select the serial port for the {interface} interface',
        *port_list
    )

    # Search through the ports to find the name of the one that was selected.
    return next(p.name for p in port_list if str(p) == selected_port)


@library(scope='GLOBAL')
class Printer:

    def __init__(self) -> None:
        self._output_path: Optional[Path] = None
        self._captures_path: Optional[Path] = None
        self._printouts_path: Optional[Path] = None

        self._mech: Optional[PrintMechAnalyzer] = None
        self._usb: Optional[BaseCommsInterface] = None
        self._rs232: Optional[SerialCommsInterface] = None
        self._ir: Optional[SerialCommsInterface] = None

    def __del__(self) -> None:
        self.shutdown()

    @keyword('Shutdown Printer')
    def shutdown(self) -> None:
        pass

    @keyword('Select Printer Mechanism Analyzer')
    def select_printer_mechanism_analyzer(
        self,
        mech: Optional[PrintMechanism] = None
    ) -> None:
        """
        Select the analyzer to use for capturing the print mechanism output.

        Parameters
        ----------
        mech : Optional[PrintMechAnalyzer]
            Print mechanism analyzer. If none is specified, the LTPD245
            Emulator will be used.

        """
        match mech:
            case PrintMechanism.EYEBALLMK1:
                self._mech = EyeballMk1()
            case PrintMechanism.LTPD245EMULATOR:
                self._mech = LTPD245Emulator()
            case _:
                self._mech = LTPD245Emulator()

        self._mech.set_capture_output_directory(self._captures_path)
        self._mech.set_printout_output_directory(self._printouts_path)

    @keyword('Select Printer USB Interface')
    def select_usb_port(self,
                        interface: Optional[USBInterface] = None
                        ) -> None:
        """
        Select a USB interface. If none is specified, open a Robot Framework
        dialog asking the user to select one.

        Parameters
        ----------
        port_name : Optional[str]
            Name of the port. e.g. 'COM6'

        Raises
        ------
        FatalError
            If devices are found with the correct VID or PID.

        """
        if not interface:
            valid_ports = USBInterface.get_valid_ports()

            if len(valid_ports) < 1:
                raise FatalError('Unable to find any printer USB connection.')

            port = get_serial_port_from_user('USB', valid_ports)
            interface = USBInterface(port)

        self._usb = interface

    @keyword('Select Printer RS232 Interface')
    def select_rs232_interface(self,
                               interface: Optional[SerialCommsInterface] = None,
                               ) -> None:
        """
        Select a RS232 interface. If none is specified, open a Robot Framework
        dialog asking the user to select one.

        Parameters
        ----------
        interface : Optional[SerialCommsInterface]
            Interface to use for RS232 communications.

        Raises
        ------
        FatalError
            If any error occurs.

        """
        if not interface:
            hardware_interface = HardwareInterface.from_user(interface='RS232')
            valid_ports = hardware_interface.get_valid_ports()

            if len(valid_ports) < 1:
                raise FatalError(
                    f'Unable to find a valid port for {hardware_interface}.'
                )

            port = get_serial_port_from_user(hardware_interface, valid_ports)
            interface = hardware_interface.get_rs232_interface(port)

        self._rs232 = interface

    @keyword('Select Printer IR Interface')
    def select_infrared_interface(self,
                                  interface: Optional[SerialCommsInterface] = None,
                                  ) -> None:
        """
        Select an IR interface. If none is specified, open a Robot Framework
        dialog asking the user to select one.

        Parameters
        ----------
        interface : Optional[SerialCommsInterface]
            Interface to use for IR communications.

        Raises
        ------
        FatalError
            If any error occurs.

        """
        if not interface:
            hardware_interface = HardwareInterface.from_user(interface='IR')
            valid_ports = hardware_interface.get_valid_ports()

            if len(valid_ports) < 1:
                raise FatalError(
                    f'Unable to find a valid port for {hardware_interface}.'
                )

            port = get_serial_port_from_user(hardware_interface, valid_ports)
            interface = hardware_interface.get_infrared_interface(port)

        self._ir = interface

    @keyword('Create Printer Library Output Directories')
    def create_output_directories(
            self,
            directory: Optional[Path] = None,
            save_mech_captures: bool = True,
            save_printouts: bool = True
    ) -> None:
        """
        Create output directories for mech analyzer records and printouts.

        Parameters
        ----------
        directory : Optional[Path]
            Directory to create the output sub-directories. If none is
            specifed, attempt to set the directory based on the ${OUTPUT DIR}
            variable in Robot Framework.

        """
        if directory:
            self._output_path = directory.absolute()
        else:
            outdir = BuiltIn().get_variable_value("${OUTPUT DIR}")
            self._output_path = Path(outdir).absolute()

        if save_mech_captures:
            self._captures_path = Path(self._output_path, 'captures')
            self._captures_path.mkdir(exist_ok=True)

        if save_printouts:
            self._printouts_path = Path(self._output_path, 'printouts')
            self._printouts_path.mkdir(exist_ok=True)

        if self._mech:
            self._mech.set_capture_output_directory(self._captures_path)
            self._mech.set_printout_output_directory(self._printouts_path)

    @keyword('Wait Until Print Complete')
    def wait_until_print_complete(self, timeout: float = 5) -> None:
        """
        Wait until a print has finished.

        Parameters
        ----------
        timeout : float
            Maximum time in seconds to wait for the print to complete.

        Raises
        ------
        ContinuableFailure
            If the print fails to complete within the given timeframe.

        """
        if self._mech:
            try:
                self._mech.wait_until_print_complete(timeout)
            except TimeoutError:
                raise ContinuableFailure(
                    'Print failed to complete within the expected timeframe'
                )
        else:
            raise Error(
                'Attempted to access print mechanism analyzer but none has ' +
                'been selected.'
            )

    @keyword('Last Printout')
    def get_last_printout(self) -> Printout:
        if self._mech:
            return self._mech.get_last_printout()
        else:
            raise Error(
                'Attempted to access print mechanism but none has ' +
                'been selected.'
            )

    @keyword('Open Printer "${interface}" Interface')
    def open_comms_interface(self, interface: CommsInterface) -> None:
        """
        Open a communication interface to the printer.

        Parameters
        ----------
        interface : CommsInterface
            The communication interface to open.

        Raises
        ------
        PrinterInterfaceError
            If an invalid interface is specified or the specified communication
            interface has not been initialised.

        """
        match interface:
            case CommsInterface.USB if self._usb is not None:
                self._usb.open()
            case CommsInterface.RS232 if self._rs232 is not None:
                self._rs232.open()
            case CommsInterface.IR if self._ir is not None:
                self._ir.open()
            case _:
                raise Error(
                    f'Cannot open {interface} interface.' +
                    'The interface has not been initialised.'
                )

    @keyword('Close Printer "${interface}" Interface')
    def close_comms_interface(self, interface: CommsInterface) -> None:
        """
        Close a communication interface to the printer.

        Parameters
        ----------
        interface : CommsInterface
            The communication interface to close.

        Raises
        ------
        Error
            If an invalid interface is specified or the specified communication
            interface has not been initialised.

        """
        match interface:
            case CommsInterface.USB if self._usb is not None:
                self._usb.close()
            case CommsInterface.RS232 if self._rs232 is not None:
                self._rs232.close()
            case CommsInterface.IR if self._ir is not None:
                self._ir.close()
            case _:
                raise Error(
                    f'Cannot close {interface} interface.' +
                    'The interface has not been initialised.'
                )

    @keyword('Set Test System "${interface}" Baud Rate To "${baud_rate}"')
    def set_baud_rate(self, interface: CommsInterface, baud_rate: int) -> None:
        match interface:
            case CommsInterface.RS232 if self._rs232:
                self._rs232.set_baud_rate(baud_rate)
            case CommsInterface.IR if self._ir is not None:
                self._ir.set_baud_rate(baud_rate)
            case _:
                raise Error(
                    f'Cannot set {interface} baud rate as the interface ' +
                    'does not exist.'
                )

    @keyword('Set Test System "${interface}" Frame Format To "${format}"')
    def set_frame_format(self,
                         interface: CommsInterface,
                         format: FrameFormat | str) -> None:
        """
        Configure the number of data bits and the parity of a communications
        interface.

        Parameters
        ----------
        interface : CommsInterface
            The communications interface to configure.

        format : FrameFormat | str
            Frame fomrat to configure the interface to use. Must be a member or
            value of a member of FrameFormat.

        Raises
        ------
        Error
            If an invalid interface is specified, the specified communication
            interface has not been initialised or if the format is invalid.

        """

        match format:
            case FrameFormat.NONE_8BITS:
                bits, parity = 8, comms.interface.Parity.NONE
            case FrameFormat.EVEN_8BITS:
                bits, parity = 8, comms.interface.Parity.EVEN
            case FrameFormat.ODD_8BITS:
                bits, parity = 8, comms.interface.Parity.ODD
            case FrameFormat.EVEN_7BITS:
                bits, parity = 7, comms.interface.Parity.EVEN
            case FrameFormat.ODD_7BITS:
                bits, parity = 7, comms.interface.Parity.ODD
            case _:
                raise Error(
                    f'{format} is not a valid FrameFormat. {os.linesep}' +
                    f'Valid formats are: {[e.value for e in FrameFormat]}'
                )

        match interface:
            case CommsInterface.RS232 if self._rs232:
                self._rs232.set_data_bits(bits)
                self._rs232.set_parity(parity)
            case CommsInterface.IR if self._ir is not None:
                self._ir.set_data_bits(bits)
                self._ir.set_parity(parity)
            case _:
                raise Error(
                    f'{interface} is not a valid communications interface to ' +
                    f'configure the frame format.'
                )

    @keyword('Print')
    def print(self,
              text: str,
              interface: CommsInterface = CommsInterface.USB,
              name: Optional[str] = None) -> None:
        """
        Print text.

        Parameters
        ----------
        text : str
            Text string to be printed.

        interface : CommsInterface
            Specifies the interface that should be used to transmit the text to
            the printer. Default is USB.

        name : Optional[str]
            An optional name given to any created files.

        Raises
        ------
        PrinterInterfaceError
            If an invalid interface is specified or the specified communication
            interface has not been initialised.

        """
        if name is None:
            name = self._get_test_name_or_none()

        if self._mech:
            self._mech.start_capture(name)

        else:
            raise Error(
                'Attempted to use print mechanism but none has been selected.'
            )

        match interface:
            case CommsInterface.USB if self._usb:
                self._usb.send(text.encode(encoding='charmap'))
                self._usb.flush()
            case CommsInterface.RS232 if self._rs232:
                self._rs232.send(text.encode(encoding='charmap'))
                self._rs232.flush()
            case CommsInterface.IR if self._ir is not None:
                self._ir.send(text.encode(encoding='charmap'))
                self._ir.flush()
            case _:
                raise Error(
                    f'Cannot print over {interface}. ' +
                    'The interface is not connected.'
                )

    @keyword('Send Printer Command')
    def send_command(self,
                     command: bytes,
                     interface: CommsInterface = CommsInterface.USB
                     ) -> None:

        match interface:
            case CommsInterface.USB if self._usb:
                self._usb.send(command)
                self._usb.flush()
            case CommsInterface.RS232 if self._rs232:
                self._rs232.send(command)
                self._rs232.flush()
            case CommsInterface.IR if self._ir is not None:
                self._ir.send(command)
                self._ir.flush()
            case _:
                raise Error(
                    f'Cannot send command over {interface}.' +
                    'The interface is not connected.'
                )

    """
    Convinience functions for sending specific commands.

    """
    @keyword('Reset Printer')
    def reset(self) -> None:
        self.send_command(COMMAND_RESET)

    @keyword('Enable Printer Debug Mode')
    def enable_debug(self) -> None:
        self.send_command(ENABLE_DEBUG)

    @keyword('Print Selftest')
    def print_selftest(self) -> None:
        if self._mech:
            self._mech.start_capture(name=self._get_test_name_or_none())
            self.send_command(DEBUG_PRINT_SELFTEST)
        else:
            raise Error(
                'Attempted to use print mechanism but none has been selected.'
            )

    @keyword('Set Printer Option')
    def set_option(self, option: int, setting: int) -> None:
        """
        Set a configuration option. The option will have no effect until the
        printer is reset.

        Parameters
        ----------
        option : int
            Option number.

        setting : int
            Setting number.

        """
        self.send_command(DEBUG_SET_OPTION + bytes([option, setting]))

    @keyword('Clear Printer Print Buffer')
    def clear_print_buffer(self) -> None:
        self.send_command(COMMAND_CLEAR_PRINT_BUFFER)

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
