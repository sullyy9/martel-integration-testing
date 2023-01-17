import weakref
from weakref import finalize
from typing import Final

import serial
from serial import Serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo

from .interface import Parity, SerialCommsInterface


class RS232Error(Exception):
    pass


class RS232Adapter(SerialCommsInterface):
    """
    Interface for a printer's RS232 connection through a USB to RS232 adapter.

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
        RS232Error
            If the specified port does not have a valid device connected.

        """
        self._port: Final[Serial]
        self.disconnect: Final[finalize]

        ports = serial.tools.list_ports.comports()
        existing_port_names = [port.name for port in ports]

        if port_name not in existing_port_names:
            raise RS232Error(
                f'Attempted to open RS232 interface on {port_name} but a port '
                f'with that name does not exist.'
            )

        self._port = Serial(port_name, timeout=2)
        self.disconnect = weakref.finalize(self, self._cleanup)

    def _cleanup(self) -> None:
        if self._port.is_open:
            self._port.close()