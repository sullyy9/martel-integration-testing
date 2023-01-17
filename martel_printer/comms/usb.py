import weakref
from weakref import finalize
from typing import Final


import serial
from serial import Serial
import serial.tools.list_ports

from .interface import SerialCommsInterface


class USBError(Exception):
    pass


class USBPort(SerialCommsInterface):
    """
    Interface for a printer's USB connection.

    Attributes
    ----------
    cleanup : finalize
        Callable to perform cleanup of class instances.

    """
    def __init__(self, port_name: str) -> None:
        """
        Open a new interface instance on the given port.

        Parameters
        ----------
        port_name : str
            Name of the port to connect to.

        Raises
        ------
        USBError
            If the specified port does not exist.

        """
        self._port: Final[Serial]
        self.disconnect: Final[finalize]

        ports = serial.tools.list_ports.comports()
        existing_port_names = [port.name for port in ports]

        if port_name not in existing_port_names:
            raise USBError from ValueError(
                f'Attempted to open USB interface on {port_name} but a port '
                f'with that name does not exist.'
            )

        self._port = Serial(port_name, timeout=1)
        self.disconnect = weakref.finalize(self, self._cleanup)

    def _cleanup(self) -> None:
        if self._port.is_open:
            self._port.close()


class USBAutoDetect(SerialCommsInterface):
    """
    Interface for a printer's USB connection.

    Attributes
    ----------
    cleanup : finalize
        Callable to perform cleanup of class instances.

    """
    _VIDS: list[int] = [0x483]
    _PIDS: list[int] = [0x1, 0x5740]

    def __init__(self) -> None:
        """
        Create a new interface instance to the given port.

        Parameters
        ----------
        port_name : str
            Name of the port to connect to.

        Raises
        ------
        USBError
            If no ports are found with a valid printer device or more than one
            printer is found. 

        """
        self._port: Final[Serial]
        self.disconnect: Final[finalize]

        ports = serial.tools.list_ports.comports()

        valid_ports = [
            port for port in ports if port.vid in self._VIDS and port.pid in self._PIDS]

        if len(valid_ports) == 0:
            raise USBError(f'Unable to autodetect printer USB port.')
        
        if len(valid_ports) > 1:
            raise USBError(
                f'Multiple potential printer USB ports detected: {valid_ports}. '
                f'Please specifiy a port.'
            )

        self._port = Serial(valid_ports[0].name, timeout=1)
        self.disconnect = weakref.finalize(self, self._cleanup)

    def _cleanup(self) -> None:
        if self._port.is_open:
            self._port.close()
