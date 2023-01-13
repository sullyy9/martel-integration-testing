import os
import weakref
import logging
from weakref import finalize
from enum import StrEnum, unique
from typing import Optional, Final

from . import comms
from .comms import SerialCommsInterface
from .common_types import ControlCode


class CommsError(Exception):
    ...


@unique
class Encoding(StrEnum):
    ASCII = 'ascii'
    UTF8 = 'utf-8'
    UTF16 = 'utf-16'


@unique
class FrameFormat(StrEnum):
    NONE_8BITS = '8 Bits None',
    EVEN_8BITS = '8 Bits Even',
    ODD_8BITS = '8 Bits Odd',
    EVEN_7BITS = '7 Bits Even',
    ODD_7BITS = '7 Bits Odd'


class Printer:
    def __init__(self, comms_interface: SerialCommsInterface) -> None:
        self.log: Final[logging.Logger] = logging.getLogger('printer')
        self._comms_interface: Optional[SerialCommsInterface] = comms_interface
        self.disconnect: Final[finalize] = weakref.finalize(
            self, self._cleanup)

        self.log.info(
            f"Creating instance with {type(self._comms_interface).__name__}"
        )

    def _cleanup(self) -> None:
        self.log.info(f"Disconnecting")

        if self._comms_interface:
            self._comms_interface.disconnect()

    def set_comms_interface(self, comms_interface: SerialCommsInterface) -> None:
        """
        Set a new communications interface. The previous interface will be
        closed before it is replaced.

        Parameters
        ----------
        comms_interface : SerialCommsInterface
            A type implementing the SerialCommsInterface protocol.

        """
        self.log.info(
            f'Setting new comms interface ' +
            f'{type(self._comms_interface).__name__}'
            )

        if self._comms_interface:
            self._comms_interface.disconnect()
        self._comms_interface = comms_interface

    def open_comms_interface(self) -> None:
        """
        Open the communications interface.

        Raises
        ------
        CommsError
            If a comms interface is not set.

        """
        self.log.info('Opening comms interface')

        if not self._comms_interface:
            raise CommsError(
                'Cannot open comms interface as non has been set'
            )
        self._comms_interface.open()

    def close_comms_interface(self) -> None:
        """
        Close the communications interface.

        Raises
        ------
        CommsError
            If a comms interface is not set.

        """
        self.log.info('Closing comms interface')

        if not self._comms_interface:
            raise CommsError(
                'Cannot close comms interface as non has been set'
            )
        self._comms_interface.close()

    def set_baud_rate(self, baud_rate: int) -> None:
        """
        Set for baud rate for the given interface.

        Parameters
        ----------
        baud_rate : int
            baud rate to set.

        Raises
        ------
        CommsError
            If a comms interface is not set.

        """
        self.log.info(f'Setting baud rate to {baud_rate}')

        if not self._comms_interface:
            raise CommsError(
                'Cannot set baud rate as no comms interface has been set'
            )

        self._comms_interface.set_baud_rate(baud_rate)

    def set_frame_format(self, format: FrameFormat | str) -> None:
        """
        Configure the number of data bits and the parity of a communications
        interface.

        Parameters
        ----------
        interface : CommsInterface
            The communications interface to configure.

        format : FrameFormat | str
            Frame fomrat to configure the interface to use. Must be a member or
            value of a member of FrameFormat.

        Raises
        ------
        CommsError
            If a comms interface is not set.

        ValueError
            If the frame format is invalid.

        """
        self.log.info(f'Setting frame format to {str(format)}')

        if not self._comms_interface:
            raise CommsError(
                'Cannot set frame format as no comms interface has been set'
            )

        match format:
            case FrameFormat.NONE_8BITS:
                bits, parity = 8, comms.interface.Parity.NONE
            case FrameFormat.EVEN_8BITS:
                bits, parity = 8, comms.interface.Parity.EVEN
            case FrameFormat.ODD_8BITS:
                bits, parity = 8, comms.interface.Parity.ODD
            case FrameFormat.EVEN_7BITS:
                bits, parity = 7, comms.interface.Parity.EVEN
            case FrameFormat.ODD_7BITS:
                bits, parity = 7, comms.interface.Parity.ODD
            case _:
                raise ValueError(
                    f'{format} is not a valid FrameFormat. {os.linesep}',
                    f'Valid formats are: {[e.value for e in FrameFormat]}'
                )

        self._comms_interface.set_data_bits(bits)
        self._comms_interface.set_parity(parity)

    def send(self, data: bytes) -> None:
        '''
        Send the given bytes to the printer.

        Parameter
        ---------
        data : bytes
            Data to send to the printer. Care should be taken to ensure the
            data is encoded in the correct format.

        Raises
        ------
        CommsError
            If a comms interface is not set.

        '''
        self.log.info(f'Sending data [{data.hex(" ").upper()}]')

        if not self._comms_interface:
            raise CommsError(
                'Cannot send data as no comms interface has been set'
            )

        self._comms_interface.send(data)
        self._comms_interface.flush()

    def print(self, text: str, encoding: Encoding = Encoding.ASCII) -> None:
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

        Raises
        ------
        CommsError
            If a comms interface is not set.

        '''
        self.log.info(f'Printing text "{text}" with encoding {encoding}')
        self.send(text.encode(encoding))

    def println(self, text: str = '', encoding: Encoding = Encoding.ASCII) -> None:
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

        Raises
        ------
        CommsError
            If a comms interface is not set.

        '''
        self.log.info(f'Printing text "{text}" with encoding {encoding}')
        self.send(text.encode(encoding))
        self.send(ControlCode.LF.to_bytes())

    def get_response(self) -> Optional[str]:
        if self._comms_interface:
            response = self._comms_interface.receive()
            if response:
                return response.decode('ascii')
