from datetime import timedelta, datetime
import weakref
import logging
from weakref import finalize
from enum import StrEnum, unique
from typing import Optional, Final

from .comms import SerialCommsInterface, Parity
from .command_set.common import ControlCode


@unique
class Encoding(StrEnum):
    CP166 = 'cp166'  # UK keyboard layout
    CP437 = 'cp437'
    ASCII = 'ascii'
    UTF8 = 'utf-8'
    UTF16 = 'utf-16'


class Printer:
    def __init__(self, comms_interface: SerialCommsInterface) -> None:
        self.log: Final[logging.Logger] = logging.getLogger('printer')

        self._comms_interface: SerialCommsInterface = comms_interface
        self._comms_interface.close()

        self.disconnect: Final[finalize] = weakref.finalize(
            self, self._cleanup)

        self.log.info(
            f"Creating instance with {type(self._comms_interface).__name__}"
        )

    def _cleanup(self) -> None:
        self.log.info(f"Disconnecting")
        self._comms_interface.disconnect()

    def configure(self,
                  baud_rate: Optional[int] = None,
                  data_bits: Optional[int] = None,
                  parity: Optional[Parity] = None,
                  ) -> None:

        self.log.info(
            f'Configuring communication interface to {baud_rate} baud, '
            f'{data_bits} bits, {parity} parity'
        )
        if baud_rate is not None:
            self._comms_interface.set_baud_rate(baud_rate)
        if data_bits is not None:
            self._comms_interface.set_data_bits(data_bits)
        if parity is not None:
            self._comms_interface.set_parity(parity)

    def send(self, data: bytes) -> None:
        '''
        Send the given bytes to the printer.

        Parameter
        ---------
        data : bytes
            Data to send to the printer. Care should be taken to ensure the
            data is encoded in the correct format.

        '''
        self.log.info(f'Sending data [{data.hex(" ").upper()}]')
        self._comms_interface.open()
        self._comms_interface.send(data)
        self._comms_interface.flush()
        self._comms_interface.close()

    def send_and_read_response(self,
                               data: bytes,
                               read_timeout: timedelta = timedelta(seconds=1),
                               read_until: Optional[str] = None) -> str:
        self._comms_interface.open()
        self._comms_interface.send(data)
        self._comms_interface.flush()

        timeout_point = datetime.now() + read_timeout

        response: str = ''
        while datetime.now() < timeout_point:
            bytes = self._comms_interface.receive()
            if bytes is not None:
                response += bytes.decode('cp437')

                if read_until and read_until in response:
                    break

        self._comms_interface.close()
        return response

    def print(self, text: str, encoding: Encoding = Encoding.CP437) -> None:
        '''
        Send the given text string to the printer. The text will be encoded
        using the given format. 

        Parameter
        ---------
        text : str
            Text to send to the printer.

        encoding : Encoding
            Encoding format to use to encode the string. Care should be taken
            to ensure this matches the encoding the printer is configured to. 

        '''
        self.log.info(f'Printing text [{text}] with [encoding={encoding}]')
        self.send(text.encode(encoding))

    def println(self, text: str = '', encoding: Encoding = Encoding.CP437) -> None:
        '''
        Send the given text string to the printer followed by a new line. The
        text will be encoded using the given format. 

        Parameter
        ---------
        text : str
            Text to send to the printer.

        encoding : Encoding
            Encoding format to use to encode the string. Care should be taken
            to ensure this matches the encoding the printer is configured to. 

        '''
        self.log.info(f'Printing text [{text}] with [encoding={encoding}]')
        self.send(text.encode(encoding))
        self.send(ControlCode.LF.to_bytes())
