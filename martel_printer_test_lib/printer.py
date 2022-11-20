import os
from enum import StrEnum, unique
from pathlib import Path
from typing import Optional

from serial.tools.list_ports_common import ListPortInfo

from robot.api import Error, FatalError
from robot.api.deco import keyword, library
from robot.libraries import Dialogs
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

import comms
from mech import PrintMechAnalyzer, LTPD245Emulator, EyeballMk1
from printout import Printout
from comms import (BaseCommsInterface, SerialCommsInterface, USBInterface,
                   RS232AdapterInterface, RS232TCUInterface)


PRINTER_VID = 0x483
PRINTER_PID = [0x1, 0x5740]

NULL = 0
ESC = 0x1B
ENABLE_DEBUG = bytearray([ESC, NULL, NULL, ord('D'), NULL])
DEBUG_PRINT_SELFTEST = bytearray([ESC, NULL, NULL, ord('S'), 8])
DEBUG_SET_OPTION = bytearray([ESC, NULL, NULL, ord('O')])

COMMAND_RESET = bytearray([ESC, NULL, ord('@')])


@unique
class CommsInterface(StrEnum):
    USB = 'USB'
    RS232 = 'RS232'
    INFRARED = 'IR'
    BLUETOOTH = 'BT'


@unique
class RS232HardwareInterface(StrEnum):
    USB_RS232_ADAPTER = 'USB To RS232 Adapter'
    TCU = 'TCU'


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


@library(scope='GLOBAL')
class Printer:

    def __init__(self) -> None:
        self._output_path: Optional[Path] = None
        self._captures_path: Optional[Path] = None
        self._printouts_path: Optional[Path] = None

        self.mech: Optional[PrintMechAnalyzer] = None
        self.usb: Optional[BaseCommsInterface] = None
        self._rs232: Optional[SerialCommsInterface] = None

    def __del__(self) -> None:
        self.shutdown()

    @keyword('Shutdown Printer')
    def shutdown(self) -> None:
        pass

    @keyword('Select Printer Mechanism')
    def select_printer_mechanism(
        self,
        mech: Optional[PrintMechAnalyzer] = None
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
                self.mech = EyeballMk1()
            case PrintMechanism.LTPD245EMULATOR | None:
                self.mech = LTPD245Emulator()

        if self.mech:
            self.mech.set_capture_output_directory(self._captures_path)
            self.mech.set_printout_output_directory(self._printouts_path)

    @keyword('Select Printer USB Port')
    def select_usb_port(self, port_name: Optional[str] = None) -> None:
        """
        Select the port to use for the USB interface. If none is specified,
        open a dialog and ask the user to select one. The dialog will only
        contain devices which have a VID and PID matching that of a printer.

        Parameters
        ----------
        port_name : Optional[str]
            Name of the port. e.g. 'COM6'

        Raises
        ------
        FatalError
            If devices are found with the correct VID or PID.

        """
        ports = USBInterface.get_valid_ports()
        if len(ports) < 1:
            raise FatalError('Unable to find any printer USB connection.')

        port_names = [port.name for port in ports]

        if port_name:
            if port_name not in port_names:
                raise FatalError(
                    'Unable to find a printer on port {port_name}.'
                )

            self.usb = USBInterface(port_name)

        else:
            selected_port = Dialogs.get_selection_from_user(
                'Select the printers USB port',
                *ports
            )

            # Search through the ports to find the name of the one that was
            # selected.
            self.usb = USBInterface(
                next(p.name for p in ports if str(p) == selected_port)
            )

    @keyword('Select Printer RS232 Port')
    def select_rs232_port(self,
                          method: Optional[RS232HardwareInterface] = None,
                          port_name: Optional[str] = None) -> None:
        """
        Select the port to use for the rs232 interface. If none is specified,
        open a dialog and ask the user to select one.

        Parameters
        ----------
        port_name : Optional[str]
            Name of the port. e.g. 'COM6'

        Raises
        ------
        FatalError
            If no ports are found with the given name.

        """
        if not method:
            method = Dialogs.get_selection_from_user(
                'Select the printers RS232 hardware interface:',
                RS232HardwareInterface.USB_RS232_ADAPTER,
                RS232HardwareInterface.TCU
            )

        valid_ports: list[ListPortInfo]
        match method:
            case RS232HardwareInterface.USB_RS232_ADAPTER:
                valid_ports = RS232AdapterInterface.get_valid_ports()
            case RS232HardwareInterface.TCU:
                valid_ports = RS232TCUInterface.get_valid_ports()
            case _:
                raise FatalError(
                    'An invalid RS232 hardware interface has been selected.'
                )

        if len(valid_ports) < 1:
            raise FatalError('Unable to find any printer RS232 connection.')

        valid_port_names = [port.name for port in valid_ports]

        # If no port has been specified, ask the user for one.
        if port_name is None:
            selected_port = Dialogs.get_selection_from_user(
                'Select the printers RS232 port',
                *valid_ports
            )

            # Search through the ports to find the name of the one that was
            # selected.
            port_name = next(p.name for p in valid_ports
                             if str(p) == selected_port)

        # If a port has been specified, make sure it's valid.
        elif port_name not in valid_port_names:
            raise FatalError('{port_name} is not a valid port.')

        if port_name:
            match method:
                case RS232HardwareInterface.USB_RS232_ADAPTER:
                    self._rs232 = RS232AdapterInterface(port_name)
                case RS232HardwareInterface.TCU:
                    self._rs232 = RS232TCUInterface(port_name)

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

        if self.mech:
            self.mech.set_capture_output_directory(self._captures_path)
            self.mech.set_printout_output_directory(self._printouts_path)

    @keyword('Wait Until Print Complete')
    def wait_until_print_complete(self) -> None:
        if self.mech:
            self.mech.wait_until_print_complete()
        else:
            raise Error(
                'Attempted to access print mechanism but none has been selected.'
            )

    @keyword('Last Printout')
    def get_last_printout(self) -> Printout:
        if self.mech:
            return self.mech.get_last_printout()
        else:
            raise Error(
                'Attempted to access print mechanism but none has been selected.'
            )

    @keyword(name='Open Printer "${interface}" Interface')
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
            case CommsInterface.USB if self.usb is not None:
                self.usb.open()
            case _:
                raise Error(
                    f'Cannot open {interface} interface.' +
                    'The interface has not been initialised.'
                )

    @keyword(name='Close Printer "${interface}" Interface')
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
            case CommsInterface.USB if self.usb is not None:
                self.usb.close()
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
            case _:
                raise Error(
                    f'{interface} is not a valid communications interface to' +
                    f'configure the frame format. {os.linesep}'
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

        if self.mech:
            self.mech.start_capture(name)

        else:
            raise Error(
                'Attempted to use print mechanism but none has been selected.'
            )

        match interface:
            case CommsInterface.USB if self.usb:
                self.usb.send(text.encode(encoding='charmap'))
                self.usb.flush()
            case CommsInterface.RS232 if self._rs232:
                self._rs232.send(text.encode(encoding='charmap'))
                self._rs232.flush()
            case _:
                raise Error(
                    f'Cannot print over {interface}. ' +
                    'The interface is not connected.'
                )

    @keyword('Send Printer Command')
    def send_command(self,
                     command: bytearray,
                     interface: CommsInterface = CommsInterface.USB
                     ) -> None:

        match interface:
            case CommsInterface.USB if self.usb:
                self.usb.send(command)
            case _:
                raise Error(
                    f'Cannot send command over {interface}.' +
                    'The interface is not connected.'
                )

    """
    Convinience functions for sending specific commands.

    """
    @keyword(name='Reset Printer')
    def reset(self) -> None:
        self.send_command(COMMAND_RESET)

    @keyword(name='Enable Printer Debug Mode')
    def enable_debug(self) -> None:
        self.send_command(ENABLE_DEBUG)

    @keyword('Print Selftest')
    def print_selftest(self) -> None:
        if self.mech:
            self.mech.start_capture(name=self._get_test_name_or_none())
            self.send_command(DEBUG_PRINT_SELFTEST)
        else:
            raise Error(
                'Attempted to use print mechanism but none has been selected.'
            )

    @keyword(name='Set Printer Option')
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
