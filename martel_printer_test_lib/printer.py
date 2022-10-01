import serial
import serial.tools.list_ports
from enum import Enum

from robot.api.deco import keyword, library
from PIL import Image

from printer_mech import LTPD245Emulator


PRINTER_VID = 0x483
PRINTER_PID = [0x1, 0x5740]

ESC = 0x1B
NULL = 0
ENABLE_DEBUG = bytearray([ESC, NULL, NULL, ord('D'), NULL])
DEBUG_PRINT_SELFTEST = bytearray([ESC, NULL, NULL, ord('S'), 8])
DEBUG_SET_OPTION = bytearray([ESC, NULL, NULL, ord('O')])

COMMAND_RESET = bytearray([ESC, ord('@')])

class Interface(Enum):
    USB = 1
    RS232 = 2
    INFRARED = 3
    BLUETOOTH = 4

class PrinterNotFound(Exception):
    pass

class InterfaceNotAvailable(Exception):
    pass

@library(scope='GLOBAL')
class Printer:

    def __init__(self):
        self.mech_emulator = LTPD245Emulator()
        self.usb = PrinterInterfaceUSB()
    
    def __del__(self):
        self.shutdown()

    def __enter__(self):
        self.usb.connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__del__()

    @keyword('Startup Printer')
    def startup(self):
        pass

    @keyword('Shutdown Printer')
    def shutdown(self):
        self.mech_emulator.end()
        self.usb.disconnect()

    @keyword('Wait Until Print Complete')
    def wait_until_print_complete(self):
        self.mech_emulator.wait_until_print_complete()

    @keyword('Last Printout')
    def get_last_printout(self) -> Image.Image:
        return self.mech_emulator.get_last_printout()

    @keyword(name='Connect To Printer Comm Interfaces')
    def init_comms(self):
        self.usb.connect()
    
    @keyword(name='Disconnect From Printer Comm Interfaces')
    def deinit_comms(self):
        self.usb.disconnect()

    @keyword('Print ${text}')
    def print(self, text: str, interface: Interface = Interface.USB):
        self.mech_emulator.start()
        match interface:
            case Interface.USB:
                self.usb.send(text.encode(encoding='ascii'))
            case Interface.RS232:
                raise InterfaceNotAvailable()
            case Interface.INFRARED:
                raise InterfaceNotAvailable()
            case Interface.BLUETOOTH:
                raise InterfaceNotAvailable()

    @keyword(name='Reset Printer')
    def reset(self):
        self.usb.send(COMMAND_RESET)

    @keyword(name='Enable Printer Debug Mode')
    def enable_debug(self):
        self.usb.send(ENABLE_DEBUG)

    @keyword('Print Selftest')
    def print_selftest(self):
        self.mech_emulator.start()
        self.usb.send(DEBUG_PRINT_SELFTEST)

    @keyword(name='Set Printer Option')
    def set_option(self, option: int, setting: int):
        self.usb.send(DEBUG_SET_OPTION + bytes([option, setting]))

class PrinterInterfaceUSB():
    def __init__(self):
        self.port_info = None
        self.port = None
    
    def __del__(self):
        if self.port is not None and self.port.isOpen():
            self.port.close()

    def connect(self):
        ports = serial.tools.list_ports.comports()
        try:
            self.port_info = next(
                port for port in ports if port.vid == PRINTER_VID and port.pid in PRINTER_PID)

            self.port = serial.Serial(self.port_info.name)
        except StopIteration as exc:
            raise PrinterNotFound(
                'Cannot find the printers serial port') from exc
    
    def disconnect(self):
        if self.port is not None and self.port.isOpen():
            self.port = self.port.close()
            self.port_info = None
            
    
    def get_port_name(self):
        if self.port_info is not None:
            return self.port_info.name

    def send(self, data: bytes):
        if self.port is not None and self.port.isOpen():
            self.port.write(data)
            self.port.flush()

    def flush(self):
        if self.port is not None and self.port.isOpen():
            self.port.flush()
    