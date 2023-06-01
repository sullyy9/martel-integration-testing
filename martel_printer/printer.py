import time
import weakref
import logging
from weakref import finalize
from enum import StrEnum, unique
from typing import Optional, Final

from .comms import CommsInterface
from .command_set.common import ControlCode


@unique
class Encoding(StrEnum):
    CP166 = "cp166"  # UK keyboard layout
    CP437 = "cp437"
    ASCII = "ascii"
    UTF8 = "utf-8"
    UTF16 = "utf-16"


class Printer:
    def __init__(self, comms_interface: CommsInterface, name: str = "Printer") -> None:
        self._log: Final[logging.Logger] = logging.getLogger(name)
        self._log.info("Creating printer instance")

        self.comms: Final[CommsInterface] = comms_interface

        self._destruct: Final[finalize] = weakref.finalize(self, self._cleanup)

        self._close_comms_if_open()

    def _cleanup(self) -> None:
        self._log.info("Disconnecting")
        self._close_comms_if_open()

    def send(self, data: bytes) -> None:
        """
        Send the given bytes to the printer.

        Parameter
        ---------
        data : bytes
            Data to send to the printer. Care should be taken to ensure the
            data is encoded in the correct format.

        """
        self._log.info(f'Sending bytes [{data.hex(" ").upper()}]')
        self._open_comms_if_closed()
        self.comms.write(data)
        self.comms.flush()
        self._close_comms_if_open()

    def send_and_get_response(
        self,
        data: bytes,
        timeout: float = 1,
        terminator: Optional[bytes] = None,
    ) -> bytes:
        self._log.info(f'Sending bytes [{data.hex(" ").upper()}]')

        self._open_comms_if_closed()
        self.comms.write(data)
        self.comms.flush()

        timeout_point = time.monotonic() + timeout

        response: bytes = bytes()
        while time.monotonic() < timeout_point:
            bytes_in: Final[int] = self.comms.in_waiting
            if bytes_in == 0:
                continue

            response += self.comms.read(bytes_in)

            if terminator and terminator in response:
                break

        self._close_comms_if_open()

        self._log.info(f'Received bytes [{response.hex(" ").upper()}]')
        return response

    def print(self, text: str, encoding: Encoding | str = Encoding.CP437) -> None:
        """
        Send the given text string to the printer. The text will be encoded
        using the given format.

        Parameter
        ---------
        text : str
            Text to send to the printer.

        encoding : Encoding
            Encoding format to use to encode the string. Care should be taken
            to ensure this matches the encoding the printer is configured to.

        """
        self._log.info(f"Printing text [{text}] with {encoding} encoding")
        self.send(text.encode(encoding))

    def println(self, text: str = "", encoding: Encoding = Encoding.CP437) -> None:
        """
        Send the given text string to the printer followed by a new line. The
        text will be encoded using the given format.

        Parameter
        ---------
        text : str
            Text to send to the printer.

        encoding : Encoding
            Encoding format to use to encode the string. Care should be taken
            to ensure this matches the encoding the printer is configured to.

        """
        self.print((text + chr(ControlCode.LF)), encoding=encoding)

    def _open_comms_if_closed(self) -> None:
        if not self.comms.is_open:
            self.comms.open()
    
    def _close_comms_if_open(self) -> None:
        if self.comms.is_open:
            self.comms.close()
