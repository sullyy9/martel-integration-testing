import serial.tools.list_ports
from typing import Final, Optional
from serial import Serial

from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Select, Label

from martel_printer.comms.interface import CommsInterface
from martel_tcu import TCU, RS232ThroughTCU, IrDAThroughTCU, BluetoothThroughTCU

from ..environment import PrinterInterface


STANDARD_PORTS: Final = [
    "COM29",
    "COM30",
    "COM31",
    "COM32",
]


class PortSelector(Container):
    class PortSelected(Message):
        def __init__(self, interface_name: str, selection: str | None) -> None:
            super().__init__()

            self.interface_name: Final[str] = interface_name
            self.selection: Final[str | None] = selection

    def __init__(self, name: str, options: list[str]) -> None:
        super().__init__()

        self._options: Final = [(s, s) for s in options]
        self._name: Final[str] = name

    def compose(self) -> ComposeResult:
        yield Label(self._name, classes="port_selector_label")
        yield Select(self._options, classes="port_selector_select")

    @on(Select.Changed)
    def port_selected(self, event: Select.Changed) -> None:
        event.stop()
        if event.value is None:
            self.post_message(self.PortSelected(self._name, event.value))

        elif type(event.value) is str:
            self.post_message(self.PortSelected(self._name, event.value))

        else:
            raise Exception("Unknown port type selcted.")


##################################################


class PortSelection(Container):
    def __init__(self) -> None:
        super().__init__()

        self.interface_ports: dict[str, Optional[str]] = dict.fromkeys(
            ["TCU", "Debug", *[i.value for i in PrinterInterface]]
        )

        self._connected_ports = serial.tools.list_ports.comports()
        self._connected_ports = [p.name for p in self._connected_ports]

    def compose(self) -> ComposeResult:
        self._connected_ports = serial.tools.list_ports.comports()
        self._connected_ports = [p.name for p in self._connected_ports]

        with Horizontal():
            with Vertical():
                yield PortSelector("TCU", self._connected_ports)

                yield PortSelector(PrinterInterface.USB, STANDARD_PORTS)
                yield PortSelector(
                    PrinterInterface.RS232, ["Through TCU", *STANDARD_PORTS]
                )

            with Vertical():
                yield PortSelector(
                    PrinterInterface.INFRARED, ["Through TCU", *STANDARD_PORTS]
                )
                yield PortSelector(PrinterInterface.BLUETOOTH, ["Through TCU"])

                yield PortSelector(
                    "Debug", [PrinterInterface.USB.value, PrinterInterface.RS232.value]
                )

    @on(PortSelector.PortSelected)
    def port_selected(self, event: PortSelector.PortSelected):
        event.stop()
        self.interface_ports[event.interface_name] = event.selection

    def get_tcu_interface(self) -> Serial | None:
        selection = self.interface_ports["TCU"]

        if selection is None:
            return None

        port = Serial()
        port.port = selection
        return port

    def get_printer_interface(
        self, interface: PrinterInterface
    ) -> CommsInterface | None:
        selection = self.interface_ports[interface]
        if selection is None:
            return None

        if selection in STANDARD_PORTS or selection in self._connected_ports:
            port = Serial()
            port.port = selection
            return port

        if selection == "Through TCU":
            tcu_port = self.get_tcu_interface()
            if tcu_port is None:
                return None

            match interface:
                case PrinterInterface.RS232:
                    return RS232ThroughTCU(TCU(tcu_port))
                case PrinterInterface.INFRARED:
                    return IrDAThroughTCU(TCU(tcu_port))
                case PrinterInterface.BLUETOOTH:
                    return BluetoothThroughTCU(TCU(tcu_port))
                case _:
                    pass
        
        raise Exception(f"Unexpected {interface} interface selected: {selection}")

    def get_debug_interface(self) -> CommsInterface | None:
        interface = self.interface_ports["Debug"]
        if interface is None:
            return None

        interface = PrinterInterface(interface)
        return self.get_printer_interface(interface)
