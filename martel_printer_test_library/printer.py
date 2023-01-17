import os
from enum import StrEnum, unique
from pathlib import Path
from typing import Optional, Self

import serial.tools.list_ports

from robot.api import Error, FatalError, ContinuableFailure, SkipExecution
from robot.api.deco import keyword, library
from robot.libraries import Dialogs
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

from martel_printer import debug_protocol_helper as debug
from martel_printer import martel_protocol_helper as martel
from martel_printer import Printer, USBPort, RS232Adapter, IrDAAdapter, Encoding
from martel_printer.comms import SerialCommsInterface, FrameFormat

from print_mech_analyser import PrintMechAnalyzer, LTPD245Emulator, EyeballMk1
from printout import Printout
from tcu import RS232TCUComms, IrDATCUComms


@unique
class Comms(StrEnum):
    USB = "USB"
    RS232 = "RS232"
    IRDA = "IrDA"
    BLUETOOTH = "Bluetooth"


@unique
class RS232HardwareInterface(StrEnum):
    USB_ADAPTER = 'USB Adapter'
    TCU_COMMS = 'TCU Comms'
    SKIP = 'Skip tests for this interface'

    @classmethod
    def from_user(cls) -> Self:
        selection = Dialogs.get_selection_from_user(
            f'Select the printers RS232 hardware interface:',
            *[interface for interface in Self]
        )
        return cls(selection)

    def request_port(self) -> Optional[SerialCommsInterface]:
        match self:
            case self.USB_ADAPTER:
                return RS232Adapter(request_serial_port('RS232'))
            case self.TCU_COMMS:
                return RS232TCUComms(request_serial_port('RS232'))
            case self.SKIP:
                return None


@unique
class IrDAHardwareInterface(StrEnum):
    USB_ADAPTER = 'USB Adapter'
    TCU_COMMS = 'TCU Comms'
    SKIP = 'Skip tests for this interface'

    @classmethod
    def from_user(cls) -> Self:
        selection = Dialogs.get_selection_from_user(
            f'Select the printers IrDA hardware interface:',
            *[interface for interface in Self]
        )
        return cls(selection)

    def request_port(self) -> Optional[SerialCommsInterface]:
        match self:
            case self.USB_ADAPTER:
                return IrDAAdapter(request_serial_port('IrDA'))
            case self.TCU_COMMS:
                return IrDATCUComms(request_serial_port('IrDA'))
            case self.SKIP:
                return None


@unique
class PrintMechanism(StrEnum):
    EYEBALLMK1 = 'Eyeball Mk1'
    LTPD245EMULATOR = 'LTPD245 Emulator'


def request_serial_port(interface: str) -> str:
    ports = serial.tools.list_ports.comports()
    selected_port = Dialogs.get_selection_from_user(
        f'Select the serial port for {interface} comms',
        *ports
    )
    # Search through the ports to find the name of the one that was selected.
    return next(p.name for p in ports if str(p) == selected_port)


@library(scope='GLOBAL')
class PrinterTestLibrary:

    def __init__(self) -> None:
        self._output_path: Optional[Path] = None
        self._captures_path: Optional[Path] = None
        self._printouts_path: Optional[Path] = None

        self._mech: Optional[PrintMechAnalyzer] = None

        self._comms: dict[Comms, Optional[Printer]] = {
            Comms.USB: None,
            Comms.RS232: None,
            Comms.IRDA: None
        }

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

    @keyword('Select Printer "${interface}" Interface')
    def select_interface(self, interface: Comms | str) -> None:
        """
        Ask the user to select the hardware interface and port for a comms 
        interface.

        Parameters
        ----------
        interface : CommsInterface
            Interface to set up.

        """
        match interface:
            case Comms.USB:
                self._comms[Comms.USB] = Printer(
                    USBPort(request_serial_port('USB')))
            case Comms.RS232:
                port = RS232HardwareInterface.from_user().request_port()
                self._comms[Comms.RS232] = Printer(port) if port else None
            case Comms.IRDA:
                port = IrDAHardwareInterface.from_user().request_port()
                self._comms[Comms.IRDA] = Printer(port) if port else None
            case _:
                raise Error(
                    f'Invalid interface specified to select printer ' +
                    f'interface keyword'
                )

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
    def open_comms_interface(self, interface: Comms) -> None:
        """
        Open a communication interface to the printer.

        Parameters
        ----------
        interface : CommsInterface
            The communication interface to open.

        Raises
        ------
        SkipExecution
            If the given interface has not been configured.

        """
        comm_interface = self._comms[interface]
        if comm_interface:
            comm_interface.open_comms_interface()
        else:
            raise SkipExecution(
                f'Skipping execution of {interface} tests as a {interface} ' +
                f'interface has not been configured.'
            )

    @keyword('Close Printer "${interface}" Interface')
    def close_comms_interface(self, interface: Comms) -> None:
        """
        Close a communication interface to the printer.

        Parameters
        ----------
        interface : CommsInterface
            The communication interface to close.

        Raises
        ------
        SkipExecution
            If the given interface has not been configured.

        """
        comm_interface = self._comms[interface]
        if comm_interface:
            comm_interface.close_comms_interface()
        else:
            raise SkipExecution(
                f'Skipping execution of {interface} tests as a {interface} ' +
                f'interface has not been configured.'
            )

    @keyword('Set Test System "${interface}" Baud Rate To "${baud_rate}"')
    def set_baud_rate(self, interface: Comms, baud_rate: int) -> None:
        """
        Set for baud rate for the given interface.

        Parameters
        ----------
        interface : CommsInterface
            The communications interface.

        baud_rate : int
            baud rate to set.

        Raises
        ------
        SkipExecution
            If the given interface has not been configured.

        """
        comm_interface = self._comms[interface]
        if comm_interface:
            comm_interface.set_baud_rate(baud_rate)
        else:
            raise SkipExecution(
                f'Skipping execution of {interface} tests as a {interface} ' +
                f'interface has not been configured.'
            )

    @keyword('Set Test System "${interface}" Frame Format To "${format}"')
    def set_frame_format(self,
                         interface: Comms,
                         format: FrameFormat | str
                         ) -> None:
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
            If an invalid frame format is specified.

        SkipExecution
            If the given interface has not been configured.

        """
        try:
            format = FrameFormat(format)
        except:
            raise Error(
                'Invalid frame format specified to set test system frame ' +
                'format keyword'
            )

        comm_interface = self._comms[interface]
        if comm_interface:
            comm_interface.set_frame_format(format)
        else:
            raise SkipExecution(
                f'Skipping execution of {interface} tests as a {interface} ' +
                f'interface has not been configured.'
            )

    @keyword('Print Text')
    def print(self,
              text: str,
              interface: Comms = Comms.USB,
              name: Optional[str] = None) -> None:
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

        name : Optional[str]
            An optional name given to any files created by the mech analyzer.

        Raises
        ------
        Error
            If a mech analyzer has not been selected.

        SkipExecution
            If the given interface has not been configured.

        """
        name = name if name else self._get_test_name_or_none()

        if not self._mech:
            raise Error(
                'Attempted to use print mechanism but none has been selected.'
            )
        self._mech.start_capture(name)

        comm_interface = self._comms[interface]
        if comm_interface:
            comm_interface.print(text, Encoding.ASCII)
            comm_interface.flush()
        else:
            raise SkipExecution(
                f'Skipping execution of {interface} tests as a {interface} ' +
                f'interface has not been configured.'
            )

    @keyword('Send Printer Command')
    def send_command(self,
                     command: bytes,
                     interface: Comms = Comms.USB
                     ) -> None:

        comm_interface = self._comms[interface]
        if comm_interface:
            comm_interface.send(command)
            comm_interface.flush()
        else:
            raise SkipExecution(
                f'Skipping execution of {interface} tests as a {interface} ' +
                f'interface has not been configured.'
            )

    """
    Convinience functions for sending specific commands.

    """
    @keyword('Reset Printer')
    def reset(self) -> None:
        self.send_command(debug.reset_command())

    @keyword('Enable Printer Debug Mode')
    def enable_debug(self) -> None:
        self.send_command(debug.enable_debug_command())

    @keyword('Print Selftest')
    def print_selftest(self) -> None:
        if self._mech:
            self._mech.start_capture(name=self._get_test_name_or_none())
            self.send_command(debug.set_channel_command(
                debug.SetChannel.PRINT_SELFTEST))
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
        self.send_command(debug.set_option_command(option, setting))

    @keyword('Clear Printer Print Buffer')
    def clear_print_buffer(self) -> None:
        self.send_command(martel.clear_print_buffer_command())

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
