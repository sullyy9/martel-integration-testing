from typing import Final
import serial

from martel_printer.command_set import debug_protocol
from martel_printer.comms import CommsInterface, Parity

from .tcu import TCU
from .types import RelayChannel, MeasureChannel, CommsMode


class CommsThroughTCU(CommsInterface):
    def __init__(self, tcu: TCU) -> None:
        self._tcu: Final = tcu
        self._response: bytes | None = None

    @property
    def baudrate(self) -> int:
        raise NotImplementedError

    @baudrate.setter
    def baudrate(self, baudrate: int) -> None:
        self._tcu.set_channel(RelayChannel.BAUD_RATE_SET, int(baudrate / 100))

    @property
    def bytesize(self) -> int:
        raise NotImplementedError

    @bytesize.setter
    def bytesize(self, bytesize: int) -> None:
        match bytesize:
            case 7:
                self._tcu.set_channel(RelayChannel.DATA_BITS_SET_7, 1)
            case 8:
                self._tcu.set_channel(RelayChannel.DATA_BITS_SET_7, 0)
            case _:
                raise ValueError(f"TCU only supports 7 or 8 data bits not {bytesize}")

    @property
    def parity(self) -> Parity | str:
        raise NotImplementedError

    @parity.setter
    def parity(self, parity: Parity) -> None:
        match parity:
            case serial.PARITY_NONE:
                self._tcu.set_channel(RelayChannel.PARITY_ENABLE, 0)
            case serial.PARITY_EVEN:
                self._tcu.set_channel(RelayChannel.PARITY_ENABLE, 1)
                self._tcu.set_channel(RelayChannel.PARITY_SET_EVEN, 1)
            case serial.PARITY_ODD:
                self._tcu.set_channel(RelayChannel.PARITY_ENABLE, 1)
                self._tcu.set_channel(RelayChannel.PARITY_SET_EVEN, 0)
            case _:
                raise ValueError(f"TCU does not support {parity} parity")

    @property
    def is_open(self) -> bool:
        return False

    @property
    def in_waiting(self) -> int:
        if self._response is not None:
            return len(self._response)

        raise NotImplementedError("TCU does not pass through received comms")

    def open(self) -> None:
        ...

    def close(self) -> None:
        self._response = None

    def read(self, size: int = 1) -> bytes:
        if self._response is not None:
            result, self._response = self._response[:size], self._response[size:]
            return result

        raise NotImplementedError("TCU does not pass through received comms")

    def write(self, data: bytes) -> None:
        # Intercept and handle measure channel commands with the "W" TCU command.
        if data.startswith(bytes([0x1B, 0, 0, ord("M")])):
            self._response = self._tcu.print_with_response(data)
            return

        self._tcu.print(data)

    def flush(self) -> None:
        pass


class RS232ThroughTCU(CommsThroughTCU):
    def open(self) -> None:
        self._tcu.set_channel(RelayChannel.COMMS_MODE_SET, CommsMode.RS232)


class IrDAThroughTCU(CommsThroughTCU):
    def open(self) -> None:
        self._tcu.set_channel(RelayChannel.COMMS_MODE_SET, CommsMode.IRDA)


class BluetoothThroughTCU(CommsThroughTCU):
    def open(self) -> None:
        self._tcu.set_channel(RelayChannel.COMMS_MODE_SET, CommsMode.BLUETOOTH)
        self._tcu.measure_channel(MeasureChannel.BLUETOOTH_CONNECT_PIN_0)
