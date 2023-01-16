import serial

from martel_printer.comms import SerialCommsInterface, Parity

from .tcu import TCU, RelayChannel, CommsMode


class RS232TCUComms(TCU, SerialCommsInterface):

    def open(self) -> None:
        """
        open the conection.

        """
        self.set_channel(RelayChannel.COMMS_MODE, CommsMode.RS232)

    def close(self) -> None:
        """
        Close the conection.

        """
        pass

    def send(self, data: bytes) -> None:
        """
        Write a number of bytes to the output buffer.

        """
        self.print(data)

    def flush(self) -> None:
        """
        Flush any data in the output buffer.

        """
        pass

    def set_baud_rate(self, baud_rate: int) -> None:
        self.set_channel(RelayChannel.BAUD_RATE, int(baud_rate / 100))

    def set_data_bits(self, data_bits: int) -> None:
        match data_bits:
            case 7:
                self.set_channel(RelayChannel.DATA_BITS, 1)
            case 8:
                self.set_channel(RelayChannel.DATA_BITS, 0)
            case _:
                raise ValueError(
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
                raise ValueError(
                    f'Attempted to set parity to an invlaid value'
                )


class IrDATCUComms(TCU, SerialCommsInterface):

    def open(self) -> None:
        """
        open the conection.

        """
        self.set_channel(RelayChannel.COMMS_MODE, CommsMode.IRDA)

    def close(self) -> None:
        """
        Close the conection.

        """
        pass

    def send(self, data: bytes) -> None:
        """
        Write a number of bytes to the output buffer.

        """
        self.print(data)

    def flush(self) -> None:
        """
        Flush any data in the output buffer.

        """

    def set_baud_rate(self, baud_rate: int) -> None:
        self.set_channel(RelayChannel.BAUD_RATE, int(baud_rate / 100))

    def set_data_bits(self, data_bits: int) -> None:
        match data_bits:
            case 7:
                self.set_channel(RelayChannel.DATA_BITS, 1)
            case 8:
                self.set_channel(RelayChannel.DATA_BITS, 0)
            case _:
                raise ValueError(
                    f'Attempted to set data bits to an invlaid value. ',
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
                raise ValueError(
                    f'Attempted to set parity to an invlaid value'
                )
