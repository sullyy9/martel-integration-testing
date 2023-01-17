import os
import weakref
from enum import IntEnum, unique
from typing import Final

import serial.tools.list_ports
from serial import Serial
from serial.tools.list_ports_common import ListPortInfo


class TCUError(Exception):
    pass


class TCUSerialError(Exception):
    pass


class TCUProtocolError(Exception):
    pass


@unique
class RelayChannel(IntEnum):
    COMMS_MODE_BIT_0 = 0x0C  # Use the COMMS_MODE channel instead.
    COMMS_MODE_BIT_1 = 0x0D  # Use the COMMS_MODE channel instead.
    COMMS_MODE_BIT_2 = 0x0E  # Use the COMMS_MODE channel instead.
    COMMS_MODE_BIT_3 = 0x0F  # Use the COMMS_MODE channel instead.

    BAUD_RATE_BIT_0 = 0x10  # Use the BAUD_RATE channel instead.
    BAUD_RATE_BIT_1 = 0x11  # Use the BAUD_RATE channel instead.
    BAUD_RATE_BIT_2 = 0x12  # Use the BAUD_RATE channel instead.
    BAUD_RATE_BIT_3 = 0x1C  # Use the BAUD_RATE channel instead.

    PARITY_ENABLE = 0x13    # 0: None, 1: See PARITY_EVEN_ODD
    PARITY_EVEN_ODD = 0x14  # 0: Odd, 1: Even

    DATA_BITS = 0x1A  # 0: 8 bits, 1: 7 bits

    COMMS_MODE = 0x40
    BAUD_RATE = 0x41


@unique
class CommsMode(IntEnum):
    """
    Communication protocols supported by the TCU for communicating with the
    printer. For use with the RelayChannel.COMMS_MODE channel.

    """
    RS232 = 0
    TTL = 1
    IRDA = 6
    RS485 = 8
    BLUETOOTH = 9


class TCU:
    """
    Interface to a TCU device over a serial port.

    Class Attributes
    ----------------
    VID : list[int]
        Valid VID's of a TCU usb device.

    PID : list[int]
        Valid PID's of a TCU usb device.

    MAX_BYTES_TX : int
        Size of the TCU's USB RX buffer. This is a cirualr buffer that if
        overflows will overwrite from the start.

    """
    VID: Final[list[int]] = [0x483]
    PID: Final[list[int]] = [0x5740]

    MAX_BYTES_TX: Final[int] = 128

    def __init__(self, port_name: str) -> None:
        """
        Create a new interface instance to the given port.

        Parameters
        ----------
        port_name : str
            Name of the port to connect to.

        Raises
        ------
        TCUSerialError
            If the PID and VID of the specified port's device doesn't match
            that of a TCU.

        """
        self._port: Final[Serial]
        self.disconnect: Final[weakref.finalize]

        ports = serial.tools.list_ports.comports()
        valid_port_names = [port.name for port in ports if
                            port.vid in TCU.VID and
                            port.pid in TCU.PID]

        if port_name not in valid_port_names:
            raise TCUSerialError(
                f'Attempted to connect to {port_name} but no valid port ' +
                f'with that name exists. {os.linesep}' +
                f'Valid ports are: {valid_port_names}'
            )

        self._port = Serial(port_name, timeout=2)
        self._close_port()

        self.disconnect = weakref.finalize(self, self._disconnect)

    def _disconnect(self) -> None:
        if self._port.is_open:
            self._port.close()

    def _open_port(self) -> None:
        if not self._port.is_open:
            self._port.open()

    def _close_port(self) -> None:
        if self._port.is_open:
            self._port.close()

    @staticmethod
    def get_valid_ports() -> list[ListPortInfo]:
        """
        Return a list of USB devices matching the VID and PID of a TCU.

        Returns
        -------
        list[ListPortInfo]
            List of devices which match a TCU's USB signature.

        """
        ports = serial.tools.list_ports.comports()
        return [port for port in ports if
                port.vid in TCU.VID and
                port.pid in TCU.PID]

    def _send_command(self, command: bytes) -> None:
        """
        Send a command to the TCU and verify that the TCU echos it back.

        Parameters
        ----------
        command : bytes
            The command to send. The TCU expects this to be terminated with a
            carriage return character.

        Raises
        ------
        TCUProtocolError
            If the TCU fails to echo back the command.

        """
        self._open_port()
        self._port.write(command)
        self._port.flush()

        response = self._port.read_until(b'\r')
        self._close_port()

        if response != command:
            raise TCUProtocolError(
                f'TCU failed to acknowledge command. {os.linesep}',
                f'Command:  {command} {os.linesep}',
                f'Response: {response} {os.linesep}'
            )

    def _get_response(self) -> int:
        """
        Await a response from the TCU and return it.

        Returns
        -------
        int
            Value returned by the TCU.

        Raises
        ------
        TCUInterfaceError
            If the USB interface has not been initialised.

        """
        self._open_port()
        response = self._port.read_until(b'\r', size=256)
        self._close_port()

        if len(response) == 0:
            raise TCUProtocolError(
                'Timeout occured while waiting for TCU response.'
            )
        elif response[-1] != '\r':
            raise TCUProtocolError(
                f'Received invalid response from TCU. {os.linesep}',
                f'Response: {response}'
            )

        return int(response, base=16)

    def close_relay(self, relay: RelayChannel) -> None:
        """
        Close a TCU relay (i.e. connect the input from the output). For
        bitfields (i.e. baud rate) this sets a bit to 1.

        Parameters
        ----------
        relay : Relay
            Relay number to open.

        """
        self._send_command(f'C{relay:0>2X}\r'.encode(encoding='charmap'))

    def open_relay(self, relay: RelayChannel) -> None:
        """
        Open a TCU relay (i.e. disconnect the input from the output). For
        bitfields (i.e. baud rate) this sets a bit to 0.

        Parameters
        ----------
        relay : Relay
            Relay number to open.

        """
        self._send_command(f'O{relay:0>2X}\r'.encode(encoding='charmap'))

    def set_channel(self, channel: int, value: int) -> None:
        """
        Set a TCU relay/channel to a given value.

        Parameters
        ----------
        channel : int
            Channel number to set.
        value : int
            Value to set the channel to.

        Raises
        ------
        Error
            If an error occurs in communicating with the TCU.

        """
        command = f'S{channel:0>2X}{value:0>4X}\r'
        self._send_command(command.encode(encoding='charmap'))

    def measure_channel(self, channel: int) -> int:
        """
        Measure a TCU channel.

        Parameters
        ----------
        channel : int
            Channel number to measure.

        Returns
        -------
        int
            Value measured on the channel.

        Raises
        ------
        TCUError
            If an error occurs in communicating with the TCU.

        """
        self._send_command(f'M{channel:0>2X}\r'.encode(encoding='charmap'))
        return self._get_response()

    def print(self, text: bytes) -> None:
        """
        Print the specified text on the device under test.

        Raises
        ------
        TCUError
            If the text length is too long.

        """

        encoded_data: str = ''
        for byte in text:
            encoded_data += f'{byte:0>2X}'

        command: bytes = f'P{len(text):0>2X}{encoded_data}\r'.encode('charmap')

        if len(command) > self.MAX_BYTES_TX:
            raise TCUError(
                f'Attempted to send {len(command)} bytes to the TCU. ' +
                'TCU can only recieve a maximum of 128 bytes at once.'
            )

        self._send_command(command)
