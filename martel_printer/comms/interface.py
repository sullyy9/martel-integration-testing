from enum import StrEnum, unique
from typing import Optional, Protocol
from weakref import finalize

import serial
from serial import Serial

@unique
class Parity(StrEnum):
    NONE = serial.PARITY_NONE
    EVEN = serial.PARITY_EVEN
    ODD = serial.PARITY_ODD

@unique
class FrameFormat(StrEnum):
    NONE_8BITS = '8 Bits None',
    EVEN_8BITS = '8 Bits Even',
    ODD_8BITS = '8 Bits Odd',
    EVEN_7BITS = '7 Bits Even',
    ODD_7BITS = '7 Bits Odd'

class BaseCommsInterface(Protocol):
    _port: Serial
    disconnect: finalize

    def open(self) -> None:
        """
        open the conection.

        """
        if not self._port.is_open:
            self._port.open()

    def close(self) -> None:
        """
        Close the conection.

        """
        if self._port.is_open:
            self._port.close()

    def send(self, data: bytes) -> None:
        """
        Write a number of bytes to the output buffer.

        """
        if self._port.is_open:
            self._port.write(data)

    def flush(self) -> None:
        """
        Flush any data in the output buffer.

        """
        if self._port.is_open:
            self._port.flush()

    def receive(self) -> Optional[bytes]:
        """
        Read all bytes from the input buffer.

        """
        if self._port.is_open:
            return self._port.read_all()
        
        return None

class SerialCommsInterface(BaseCommsInterface, Protocol):
    def set_baud_rate(self, baud_rate: int) -> None:
        self._port.baudrate = baud_rate

    def set_data_bits(self, data_bits: int) -> None:
        self._port.bytesize = data_bits

    def set_parity(self, parity: Parity) -> None:
        self._port.parity = parity
