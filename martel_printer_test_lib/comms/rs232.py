import os
import weakref
from weakref import finalize
from typing import Final

import serial
from serial import Serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo

from .interface import Parity, SerialCommsInterface
from .tcu import TCU, RelayChannel, TCUError


class RS232Error(Exception):
    pass

class RS232AdapterInterface(SerialCommsInterface):
    """
    Interface for a printer's RS232 connection through a USB to RS232 adapter.

    Attributes
    ----------
    cleanup : finalize
        Callable to perform cleanup of class instances.

    """
    __slots__ = ('_port', 'cleanup')

    def __init__(self, port_name: str) -> None:
        """
        Create a new interface instance to the given port.

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
        self.cleanup: Final[finalize]

        ports = serial.tools.list_ports.comports()
        valid_port_names = [port.name for port in ports]

        if port_name not in valid_port_names:
            raise RS232Error(
                f'Attempted to connect to {port_name}. ',
                'However a port with that name does not exist.'
            )

        self._port = Serial(port_name, timeout=2)
        self.cleanup = weakref.finalize(self, self._cleanup)

    def _cleanup(self) -> None:
        if self._port.isOpen():
            self._port.close()

    @staticmethod
    def get_valid_ports() -> list[ListPortInfo]:
        """
        Return a list of all ports with connected devices.

        Returns
        -------
        list[ListPortInfo]
            List of ports.

        """
        return serial.tools.list_ports.comports()


class RS232TCUInterface(TCU, SerialCommsInterface):

    def open(self) -> None:
        """
        open the conection.

        """
        if not self._port.isOpen():
            self._port.open()

    def close(self) -> None:
        """
        Close the conection.

        """
        if self._port.isOpen():
            self._port.close()

    def send(self, data: bytes) -> None:
        """
        Write a number of bytes to the output buffer.

        """
        if self._port.isOpen():
            self.print(data)

    def flush(self) -> None:
        """
        Flush any data in the output buffer.

        """
        if self._port.isOpen():
            self._port.flush()

    def set_baud_rate(self, baud_rate: int) -> None:
        self.set_channel(RelayChannel.BAUD_RATE, int(baud_rate / 100))

    def set_data_bits(self, data_bits: int) -> None:
        match data_bits:
            case 7:
                self.set_channel(RelayChannel.DATA_BITS, 1)
            case 8:
                self.set_channel(RelayChannel.DATA_BITS, 0)
            case _:
                raise TCUError(
                    f'Attempted to set data bits to an invlaid value',
                    f'Value: {data_bits}bits'
                )

    def set_parity(self, parity: Parity) -> None:
        match parity:
            case serial.PARITY_NONE:
                self.set_channel(RelayChannel.PARITY_ENABLE, 0)
            case serial.PARITY_EVEN:
                self.set_channel(RelayChannel.PARITY_ENABLE, 1)
                self.set_channel(RelayChannel.PARITY_EVEN_ODD, 1)
            case serial.PARITY_ODD:
                self.set_channel(RelayChannel.PARITY_ENABLE, 1)
                self.set_channel(RelayChannel.PARITY_EVEN_ODD, 0)
            case _:
                raise TCUError(
                    f'Attempted to set parity to an invlaid value'
                )
