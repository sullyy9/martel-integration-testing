from typing import Optional, Protocol

class CommunicationInterface(Protocol):
    @staticmethod
    def get_valid_ports() -> None:
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


    def send(self, data: bytes) -> None:
        """
        Write a number of bytes to the output buffer.

        """
        ...

    def flush(self) -> None:
        """
        Flush any data in the output buffer.

        """
        ...
    
    def receive(self) -> Optional[bytes]:
        """
        Read all bytes from the input buffer.

        """
        ...
    