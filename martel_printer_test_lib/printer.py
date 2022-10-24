from enum import Enum

import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo

from robot.api import Error, FatalError
from robot.api.deco import keyword, library
from robot.libraries import Dialogs

from printer_mech import LTPD245Emulator
from printout import Printout


PRINTER_VID = 0x483
PRINTER_PID = [0x1, 0x5740]

ESC = 0x1B
NULL = 0
ENABLE_DEBUG = bytearray([ESC, NULL, NULL, ord('D'), NULL])
DEBUG_PRINT_SELFTEST = bytearray([ESC, NULL, NULL, ord('S'), 8])
DEBUG_SET_OPTION = bytearray([ESC, NULL, NULL, ord('O')])

COMMAND_RESET = bytearray([ESC, ord('@')])


class Interface(str, Enum):
    USB = 'USB'
    RS232 = 'RS232'
    INFRARED = 'IR'
    BLUETOOTH = 'BT'


class PrinterInterfaceError(Exception):
    pass


@library(scope='GLOBAL')
class Printer:

    def __init__(self) -> None:
        self.mech_emulator = LTPD245Emulator()
        self.usb = None

    def __del__(self) -> None:
        self.shutdown()

    def __enter__(self) -> 'Printer':
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.__del__()

    @keyword('Startup Printer')
    def startup(self) -> None:
        pass

    @keyword('Shutdown Printer')
    def shutdown(self) -> None:
        self.mech_emulator.end()
        if self.usb is not None:
            self.usb.disconnect()

    @keyword('Wait Until Print Complete')
    def wait_until_print_complete(self) -> None:
        self.mech_emulator.wait_until_print_complete()

    @keyword('Last Printout')
    def get_last_printout(self) -> Printout:
        return self.mech_emulator.get_last_printout()

    @keyword(name='Ask User To Select Printer USB Port')
    def select_usb_port(self) -> None:
        """
        Open a dialog and ask the user to select which USB port the printer
        is connected to. The dialog will only contain devices which have a VID
        and PID matching that of a printer.

        Raises
        ------
        FatalError
            If devices are found with the correct VID or PID.

        """
        ports = PrinterInterfaceUSB.find_devices()
        if len(ports) < 1:
            raise FatalError('Unable to find any printer USB connection.')

        port_names = [port.name for port in ports]
        port_name = Dialogs.get_selection_from_user(
            'Select the printers USB port',
            *port_names
        )

        self.usb = PrinterInterfaceUSB(port_name)

    @keyword(name='Open Printer ${interface} Interface')
    def open_comms_interface(self, interface: Interface) -> None:
        """
        Open a communication interface to the printer.

        Parameters
        ----------
        interface : Interface
            The communication interface to open.

        Raises
        ------
        PrinterInterfaceError
            If an invalid interface is specified or the specified communication
            interface has not been initialised.

        """
        match interface:
            case Interface.USB if self.usb is not None:
                self.usb.connect()
            case _:
                raise Error(
                    f'Cannot open {interface} interface.' +
                    'The interface has not been initialised.'
                )

    @keyword(name='Close Printer ${interface} Interface')
    def close_comms_interface(self, interface: Interface) -> None:
        """
        Close a communication interface to the printer.

        Parameters
        ----------
        interface : Interface
            The communication interface to close.

        Raises
        ------
        PrinterInterfaceError
            If an invalid interface is specified or the specified communication
            interface has not been initialised.

        """
        match interface:
            case Interface.USB if self.usb is not None:
                self.usb.disconnect()
            case _:
                raise Error(
                    f'Cannot close {interface} interface.' +
                    'The interface has not been initialised.'
                )

    @keyword('Print ${text}')
    def print(self, text: str, interface: Interface = Interface.USB) -> None:
        """
        Print text.

        Parameters
        ----------
        text : str
            Text string to be printed.

        interface : Interface
            Specifies the interface that should be used to transmit the text to
            the printer. Default is USB.

        Raises
        ------
        PrinterInterfaceError
            If an invalid interface is specified or the specified communication
            interface has not been initialised.

        """
        match interface:
            case Interface.USB if self.usb is not None:
                self.mech_emulator.start()
                self.usb.send(text.encode(encoding='ascii'))
            case _:
                raise Error(
                    f'Cannot print over {interface}.' +
                    'The interface is not connected.'
                )

    @keyword('Send Printer Command')
    def send_command(self, command: bytearray, interface: Interface = Interface.USB) -> None:
        match interface:
            case Interface.USB if self.usb is not None:
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
        self.mech_emulator.start()
        self.send_command(DEBUG_PRINT_SELFTEST)

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


class PrinterInterfaceUSB():
    VIDs: list[int] = [0x483]
    PIDs: list[int] = [0x1, 0x5740]

    def __init__(self, port_name: str) -> None:
        ports = serial.tools.list_ports.comports()
        if port_name not in [port.name for port in ports]:
            raise PrinterInterfaceError(
                f'Attempted to connect to {port_name}.'
                'However a port with that name does not exist.'
            )

        self.port_info = next(port for port in ports if port.name == port_name)
        self.port = serial.Serial(port_name)

    def __del__(self) -> None:
        if self.port.isOpen():
            self.port.close()

    @staticmethod
    def find_devices() -> list[ListPortInfo]:
        """
        Return a list of USB devices matching the VID and PID of a printer.

        Returns
        -------
        list[ListPortInfo]
            List of devices which match a printer's USB signature.

        """
        ports = serial.tools.list_ports.comports()
        return [port for port in ports if
                port.vid in PrinterInterfaceUSB.VIDs and
                port.pid in PrinterInterfaceUSB.PIDs]

    def connect(self) -> None:
        if not self.port.isOpen():
            self.port.open()

    def disconnect(self) -> None:
        if self.port.isOpen():
            self.port.close()

    def get_port_name(self) -> None:
        return self.port_info.name

    def send(self, data: bytes) -> None:
        if self.port.isOpen():
            self.port.write(data)
            self.port.flush()

    def flush(self) -> None:
        if self.port.isOpen():
            self.port.flush()
