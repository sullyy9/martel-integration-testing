import weakref
import logging
from typing import Final

from serial import Serial

from .types import RelayChannel, MeasureChannel


class TCUNotResponding(Exception):
    pass


class TCUProtocolError(Exception):
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
        self._log.info("Shutting down TCU instance")
        self._close_comms_if_open()

    def open_relay(self, relay: RelayChannel) -> None:
        """
        Open a TCU relay. For bitfields (i.e. baud rate) this sets a bit to 0.

        Parameters
        ----------
        relay : Relay
            Relay number to open.

        """
        self._log.info(f"Opening relay {relay.name}")

        self._open_comms_if_closed()
        self._send_command(f"O{relay:0>2X}\r".encode(encoding="charmap"))
        self._close_comms_if_open()

    def close_relay(self, relay: RelayChannel) -> None:
        """
        Close a TCU relay. For bitfields (i.e. baud rate) this sets a bit to 1.

        Parameters
        ----------
        relay : Relay
            Relay number to open.

        """
        self._log.info(f"Closing relay {relay.name}")

        self._open_comms_if_closed()
        self._send_command(f"C{relay:0>2X}\r".encode(encoding="charmap"))
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
        self._log.info(f"Setting channel {channel.name} to {value}")
        command = f"S{channel.value:0>2X}{value:0>4X}\r"

        self._open_comms_if_closed()
        self._send_command(command.encode(encoding="charmap"))
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
        self._log.info(f"Measuring channel {channel.name}")

        self._open_comms_if_closed()
        self._send_command(f"M{channel:0>2X}\r".encode(encoding="ascii"))
        response = int(self._get_response(), base=16)
        self._close_comms_if_open()

        self._log.info(f"Channel {channel.name} measurement={response}")
        return response

    def print(self, text: bytes) -> None:
        """
        Print the specified text on the device under test.

        Raises
        ------
        ValueError
            If the text length is too long.

        """

        self._log.info(f"Printing [{text.hex(' ').upper()}]")

        encoded_data: str = ""
        for byte in text:
            encoded_data += f"{byte:0>2X}"

        command: bytes = f"P{len(text):0>2X}{encoded_data}\r".encode("cp437")

        if len(command) > self.MAX_BYTES_TX:
            raise ValueError(
                f"Attempted to send {len(command)} bytes to the TCU. "
                "TCU can only recieve a maximum of 128 bytes at once."
            )

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

        self._log.info(f"Printing [{text.hex(' ').upper()}] and expecting response")

        encoded_data: str = ""
        for byte in text:
            encoded_data += f"{byte:0>2X}"

        command: bytes = f"W{len(text):0>2X}{encoded_data}\r".encode("cp437")

        if len(command) > self.MAX_BYTES_TX:
            raise ValueError(
                f"Attempted to send {len(command)} bytes to the TCU. "
                "TCU can only recieve a maximum of 128 bytes at once."
            )

        self._open_comms_if_closed()
        self._send_command(command)
        response: Final = self._get_response()
        self._close_comms_if_open()

        return response

    def _open_comms_if_closed(self) -> None:
        self._log.debug("Opening comms")

        if not self._comms.is_open:
            self._comms.open()

    def _close_comms_if_open(self) -> None:
        self._log.debug("Closing comms")

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
        self._log.debug(f"Sending command [{command}]")

        self._comms.write(command)
        self._comms.flush()

        response: bytes = self._comms.read_until(b"\r")

        if response != command:
            self._log.error(f"Command not acknowledged. response={response}\n")
            raise TCUNotResponding(
                f"TCU failed to acknowledge command.\n"
                f"command={command}\n"
                f"response={response}\n"
            )

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
        self._log.debug("Awaiting response")

        response: bytes = self._comms.read_until(b"\r", size=256)

        if len(response) == 0:
            print(response)
            self._log.error("Timeout occured while awaiting response")
            raise TCUNotResponding("Timeout occured while awaiting TCU response.")

        elif not response.endswith(b"\r"):
            self._log.error(f"Received invalid response. response=[{response}]")
            raise TCUProtocolError(
                f"Received invalid response from TCU.\n" f"response=[{response}]"
            )

        self._log.debug(f"Got response [{response}]")
        return response
