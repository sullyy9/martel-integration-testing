from enum import Enum

from robot.api import Error, FatalError
from robot.api.deco import keyword, library
from robot.libraries import Dialogs

from printer_components.interface_usb import USBInterface
from printer_components.print_mechanism import LTPD245Emulator

from printout import Printout


PRINTER_VID = 0x483
PRINTER_PID = [0x1, 0x5740]

ESC = 0x1B
NULL = 0
ENABLE_DEBUG = bytearray([ESC, NULL, NULL, ord('D'), NULL])
DEBUG_PRINT_SELFTEST = bytearray([ESC, NULL, NULL, ord('S'), 8])
DEBUG_SET_OPTION = bytearray([ESC, NULL, NULL, ord('O')])

COMMAND_RESET = bytearray([ESC, ord('@')])


class CommsInterface(str, Enum):
    USB = 'USB'
    RS232 = 'RS232'
    INFRARED = 'IR'
    BLUETOOTH = 'BT'


@library(scope='GLOBAL')
class Printer:

    def __init__(self) -> None:
        self.mech = LTPD245Emulator()
        self.usb = None

    def __del__(self) -> None:
        self.shutdown()

    @keyword('Startup Printer')
    def startup(self) -> None:
        pass

    @keyword('Shutdown Printer')
    def shutdown(self) -> None:
        self.mech.end()
        if self.usb is not None:
            self.usb.disconnect()

    @keyword('Wait Until Print Complete')
    def wait_until_print_complete(self) -> None:
        self.mech.wait_until_print_complete()

    @keyword('Last Printout')
    def get_last_printout(self) -> Printout:
        return self.mech.get_last_printout()

    @keyword('Ask User To Select Printer USB Port')
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
        ports = USBInterface.find_devices()
        if len(ports) < 1:
            raise FatalError('Unable to find any printer USB connection.')

        port_names = [port.name for port in ports]
        port_name = Dialogs.get_selection_from_user(
            'Select the printers USB port',
            *port_names
        )

        self.usb = USBInterface(port_name)

    @keyword(name='Open Printer ${interface} Interface')
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
                self.usb.connect()
            case _:
                raise Error(
                    f'Cannot open {interface} interface.' +
                    'The interface has not been initialised.'
                )

    @keyword(name='Close Printer ${interface} Interface')
    def close_comms_interface(self, interface: CommsInterface) -> None:
        """
        Close a communication interface to the printer.

        Parameters
        ----------
        interface : CommsInterface
            The communication interface to close.

        Raises
        ------
        PrinterInterfaceError
            If an invalid interface is specified or the specified communication
            interface has not been initialised.

        """
        match interface:
            case CommsInterface.USB if self.usb is not None:
                self.usb.disconnect()
            case _:
                raise Error(
                    f'Cannot close {interface} interface.' +
                    'The interface has not been initialised.'
                )

    @keyword('Print ${text}')
    def print(self, text: str, interface: CommsInterface = CommsInterface.USB) -> None:
        """
        Print text.

        Parameters
        ----------
        text : str
            Text string to be printed.

        interface : CommsInterface
            Specifies the interface that should be used to transmit the text to
            the printer. Default is USB.

        Raises
        ------
        PrinterInterfaceError
            If an invalid interface is specified or the specified communication
            interface has not been initialised.

        """
        match interface:
            case CommsInterface.USB if self.usb is not None:
                self.mech.start()
                self.usb.send(text.encode(encoding='ascii'))
            case _:
                raise Error(
                    f'Cannot print over {interface}.' +
                    'The interface is not connected.'
                )

    @keyword('Send Printer Command')
    def send_command(self, command: bytearray, interface: CommsInterface = CommsInterface.USB) -> None:
        match interface:
            case CommsInterface.USB if self.usb is not None:
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
        self.mech.start()
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
