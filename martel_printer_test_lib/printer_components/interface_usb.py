import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo

class PrinterInterfaceError(Exception):
    pass

class USBInterface():
    VIDs: list[int] = [0x483]
    PIDs: list[int] = [0x1, 0x5740]

    def __init__(self, port_name: str) -> None:
        ports = serial.tools.list_ports.comports()
        if port_name not in [port.name for port in ports]:
            raise PrinterInterfaceError(
                f'Attempted to connect to {port_name}. ',
                'However a port with that name does not exist.'
            )

        self.port_info = next(port for port in ports if port.name == port_name)
        self.port = serial.Serial(port_name)

    def __del__(self) -> None:
        if self.port.isOpen():
            self.port.close()

    @staticmethod
    def find_devices() -> list[ListPortInfo]:
        """
        Return a list of USB devices matching the VID and PID of a printer.

        Returns
        -------
        list[ListPortInfo]
            List of devices which match a printer's USB signature.

        """
        ports = serial.tools.list_ports.comports()
        return [port for port in ports if
                port.vid in USBInterface.VIDs and
                port.pid in USBInterface.PIDs]

    def connect(self) -> None:
        if not self.port.isOpen():
            self.port.open()

    def disconnect(self) -> None:
        if self.port.isOpen():
            self.port.close()

    def get_port_name(self) -> None:
        return self.port_info.name

    def send(self, data: bytes) -> None:
        if self.port.isOpen():
            self.port.write(data)
            self.port.flush()

    def flush(self) -> None:
        if self.port.isOpen():
            self.port.flush()
