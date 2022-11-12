from typing import Optional, Protocol, Final

from serial import Serial

class CommunicationInterface(Protocol):
    _port: Serial

    @staticmethod
    def get_valid_ports() -> None:
        ...

    def open(self) -> None:
        """
        open the conection.

        """
        if not self._port.isOpen():
            self._port.open()
    
    def close(self) -> None:
        """
        Close the conection.

        """
        if self._port.isOpen():
            self._port.close()


    def send(self, data: bytes) -> None:
        """
        Write a number of bytes to the output buffer.

        """
        if self._port.isOpen():
            self._port.write(data)
            self._port.flush()

    def flush(self) -> None:
        """
        Flush any data in the output buffer.

        """
        if self._port.isOpen():
            self._port.flush()
    
    def receive(self) -> Optional[bytes]:
        """
        Read all bytes from the input buffer.

        """
        return self._port.read_all()
    