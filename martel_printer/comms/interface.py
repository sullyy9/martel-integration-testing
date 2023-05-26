from enum import StrEnum, unique
from typing import Optional, Protocol

import serial


@unique
class Parity(StrEnum):
    NONE = serial.PARITY_NONE
    EVEN = serial.PARITY_EVEN
    ODD = serial.PARITY_ODD


class CommsInterface(Protocol):
    @property
    def baudrate(self) -> int:
        ...

    @baudrate.setter
    def baudrate(self, baudrate: int) -> None:
        ...

    @property
    def bytesize(self) -> int:
        ...

    @bytesize.setter
    def bytesize(self, bytesize: int) -> None:
        ...

    @property
    def parity(self) -> Parity | str:
        ...

    @parity.setter
    def parity(self, parity: Parity) -> None:
        ...

    @property
    def is_open(self) -> bool:
        ...

    @property
    def in_waiting(self) -> int:
        ...

    def open(self) -> None:
        """
        open the conection.

        """
        ...

    def close(self) -> None:
        """
        Close the conection.

        """
        ...

    def read(self, size: int = 1) -> bytes:
        """
        Read a number of bytes from the input buffer.

        """
        ...

    def write(self, data, /) -> Optional[int]:
        """
        Write a number of bytes to the output buffer.

        """
        ...

    def flush(self) -> None:
        """
        Flush any data in the output buffer.

        """
        ...
