import weakref
from weakref import finalize
from typing import Final, Optional


import serial
from serial import Serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo

from .interface import CommunicationInterface

class USBConnectError(Exception):
    pass

class USBInterface(CommunicationInterface):
    """
    Interface for a printer's USB connection.

    Attributes
    ----------
    cleanup : finalize
        Callable to perform cleanup of class instances.

    """
    __slots__ = ('_port', 'cleanup')

    _VIDS: list[int] = [0x483]
    _PIDS: list[int] = [0x1, 0x5740]

    def __init__(self, port_name: str) -> None:
        """
        Create a new interface instance to the given port.

        Parameters
        ----------
        port_name : str
            Name of the port to connect to.

        Raises
        ------
        PrinterConnectError
            If the specified port does not have a valid device connected.

        """
        self._port: Final[Serial]
        self.cleanup: Final[finalize] 

        ports = serial.tools.list_ports.comports()
        valid_port_names = [port.name for port in ports]

        if port_name not in valid_port_names:
            raise USBConnectError(
                f'Attempted to connect to {port_name}. ',
                'However a port with that name does not exist.'
            )

        self._port = Serial(port_name, timeout = 1)
        self.cleanup = weakref.finalize(self, self._cleanup)

    def _cleanup(self) -> None:
        if self._port.isOpen():
            self._port.close()

    @staticmethod
    def get_valid_ports() -> list[ListPortInfo]:
        """
        Return a list of all ports where the device VID and PID matches that of
        a printer.

        Returns
        -------
        list[ListPortInfo]
            List of ports.

        """
        ports = serial.tools.list_ports.comports()
        return [port for port in ports if
                port.vid in USBInterface._VIDS and
                port.pid in USBInterface._PIDS]

    def open(self) -> None:
        if not self._port.isOpen():
            self._port.open()

    def close(self) -> None:
        if self._port.isOpen():
            self._port.close()

    def send(self, data: bytes) -> None:
        if self._port.isOpen():
            self._port.write(data)
            self._port.flush()

    def flush(self) -> None:
        if self._port.isOpen():
            self._port.flush()

    def receive(self) -> Optional[bytes]:
        return self._port.read_all()
