import time
import weakref
import logging
from typing import Final

from serial import Serial

from .types import RelayChannel, MeasureChannel


class NotRespondingError(Exception):
    pass


class NotAcknowldgedError(Exception):
    pass


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
    ACKNOWLDGE_TIMEOUT: Final[float] = 5.0
    RESPONSE_TIMEOUT: Final[float] = 5.0

    BYTE_ENCODING: Final[str] = "cp437"

    def __init__(self, comms_interface: Serial, name: str = "TCU") -> None:
        """
        Create a new interface instance to the given port.

        Parameters
        ----------
        comms_interface : Serial
            TCU's serial port.

        """
        self._log: Final[logging.Logger] = logging.getLogger(name)
        self._log.info("Creating new TCU instance")

        self._comms: Final = comms_interface
        self._destruct: Final = weakref.finalize(self, self._cleanup)

        self._close_comms_if_open()

    def _cleanup(self) -> None:
        self._log.info("Closing TCU instance")
        self._close_comms_if_open()

    def open_relay(self, relay: RelayChannel) -> None:
        """
        Open a TCU relay. For bitfields (i.e. baud rate) this sets a bit to 0.

        Parameters
        ----------
        relay : Relay
            Relay number to open.

        """
        self._log.info(f"Opening TCU relay.\n" f"Relay: {relay.name}")

        self._open_comms_if_closed()
        self._send_command(f"O{relay:0>2X}\r".encode(self.BYTE_ENCODING))
        self._close_comms_if_open()

    def close_relay(self, relay: RelayChannel) -> None:
        """
        Close a TCU relay. For bitfields (i.e. baud rate) this sets a bit to 1.

        Parameters
        ----------
        relay : Relay
            Relay number to open.

        """
        self._log.info(f"Closing TCU relay.\n" f"Relay: {relay.name}")

        self._open_comms_if_closed()
        self._send_command(f"C{relay:0>2X}\r".encode(self.BYTE_ENCODING))
        self._close_comms_if_open()

    def set_channel(self, channel: RelayChannel, value: int) -> None:
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
        self._log.info(
            f"Setting TCU channel.\n"
            f"Channel: {channel.name}\n"
            f"Channel value: {value}"
        )

        command = f"S{channel.value:0>2X}{value:0>4X}\r".encode(self.BYTE_ENCODING)

        self._open_comms_if_closed()
        self._send_command(command)
        self._close_comms_if_open()

    def measure_channel(self, channel: MeasureChannel) -> int:
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

        """
        self._log.info(f"Measuring TCU channel.\n" f"Channel: {channel.name}")

        self._open_comms_if_closed()
        self._send_command(f"M{channel:0>2X}\r".encode(self.BYTE_ENCODING))
        response: Final = int(self._get_response(), base=16)
        self._close_comms_if_open()

        self._log.info(
            f"Measured TCU channel.\n"
            f"Channel: {channel.name}\n"
            f"Measurement: {response}"
        )
        return response

    def print(self, text: bytes) -> None:
        """
        Print the specified text on the device under test.

        Raises
        ------
        ValueError
            If the text length is too long.

        """

        self._log.info(f"Printing [{text.hex(' ').upper()}] via TCU")

        encoded_data: str = text.hex().upper()
        command: bytes = f"P{len(text):0>2X}{encoded_data}\r".encode(self.BYTE_ENCODING)

        self._open_comms_if_closed()
        self._send_command(command)
        self._close_comms_if_open()

    def print_with_response(self, text: bytes) -> bytes:
        """
        Send the given text to the printer and wait up to 10 seconds for a 4 byte
        response.

        Raises
        ------
        ValueError
            If the text length is too long.

        """

        self._log.info(
            f"Printing [{text.hex(' ').upper()}] via TCU and expecting response"
        )

        encoded_data: str = text.hex().upper()
        command: bytes = f"W{len(text):0>2X}{encoded_data}\r".encode(self.BYTE_ENCODING)

        self._open_comms_if_closed()
        self._send_command(command)
        response: Final = self._get_response()
        self._close_comms_if_open()

        self._log.info(f"Received response from TCU [{response.hex(' ').upper()}]")
        return response

    def _open_comms_if_closed(self) -> None:
        self._log.debug("Opening TCU comms")

        if not self._comms.is_open:
            self._comms.open()

    def _close_comms_if_open(self) -> None:
        self._log.debug("Closing TCU comms")

        if self._comms.is_open:
            self._comms.close()

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
        TCUNotResponding
            If the TCU fails to echo back the command.

        """
        self._log.debug(f"Sending command to TCU [{command.hex(' ').upper()}]")

        if len(command) > self.MAX_BYTES_TX:
            raise ValueError(
                "TCU command too long.\n"
                f"Command length: {len(command)} bytes.\n"
                "Commands should be 128 bytes at most to avoid TCU buffer overflow."
            )

        self._comms.write(command)
        self._comms.flush()

        # Wait for the TCU to acknowledge the command.
        timeout_point = time.monotonic() + self.ACKNOWLDGE_TIMEOUT
        response: bytes = bytes()
        while response != command:
            if not command.startswith(response):
                raise NotAcknowldgedError(
                    "TCU failed to acknowledge command.\n"
                    f"Expected: [{command.hex(' ').upper()}]\n"
                    f"Received: [{response.hex(' ').upper()}]\n"
                    "Response should match the command but does not."
                )

            if time.monotonic() > timeout_point:
                raise NotAcknowldgedError(
                    "TCU failed to acknowledge command.\n"
                    f"Expected: [{command.hex(' ').upper()}]\n"
                    f"Received: [{response.hex(' ').upper()}]\n"
                    "Full acknowledgement not received within timeout period."
                )

            if self._comms.in_waiting > 0:
                response += self._comms.read()

        self._log.debug("Command acknowledged by TCU.")

    def _get_response(self) -> bytes:
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
        self._log.debug("Awaiting response from TCU")

        timeout_point = time.monotonic() + self.RESPONSE_TIMEOUT
        response: bytes = bytes()
        while not response.endswith(b"\r"):
            if time.monotonic() > timeout_point:
                raise NotRespondingError(
                    "TCU failed to return response.\n"
                    f"Response: [{response.hex(' ').upper()}]\n"
                    "Full CR terminated response not received within timeout period."
                )

            if self._comms.in_waiting > 0:
                response += self._comms.read()

        self._log.debug(f"Got response from TCU [{response.hex(' ').upper()}]")
        return response
