from enum import Enum, StrEnum, auto
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


STANDARD_PORTS: Final = [
    "COM29",
    "COM30",
    "COM31",
    "COM32",
]


class Selector(StrEnum):
    TCU = "TCU"
    USB = "USB"
    RS232 = "RS232"
    INFRARED = "Infrared"
    BLUETOOTH = "Bluetooth"
    DEBUG = "Debug"


class PortSelector(Container):
    class PortSelected(Message):
        def __init__(self, selector: Selector, selection: str | None) -> None:
            super().__init__()

            self.selector: Final[Selector] = selector
            self.selection: Final[str | None] = selection

    def __init__(self, name: Selector, options: list[str]) -> None:
        super().__init__()

        self._options: Final = [(s, s) for s in options]
        self._name: Final[Selector] = name

    def compose(self) -> ComposeResult:
        yield Label(self._name, classes="port_selector_label")
        yield Select(self._options, classes="port_selector_select")

    @on(Select.Changed)
    def port_selected(self, event: Select.Changed) -> None:
        if not isinstance(event.value, (type(None), Selector, str)):
            raise Exception("Unknown port type selcted.")

        event.stop()
        self.post_message(self.PortSelected(self._name, event.value))


##################################################


class PortSelection(Container):
    def __init__(self) -> None:
        super().__init__()

        self.interface_ports: dict[StrEnum, Optional[str]] = dict.fromkeys(Selector)

        self._active_ports = self._get_active_ports()

    def compose(self) -> ComposeResult:
        self._active_ports = self._get_active_ports()

        with Horizontal():
            with Vertical():
                yield PortSelector(Selector.TCU, self._active_ports)
                yield PortSelector(Selector.USB, STANDARD_PORTS)
                yield PortSelector(Selector.RS232, ["Through TCU", *STANDARD_PORTS])

            with Vertical():
                yield PortSelector(Selector.INFRARED, ["Through TCU", *STANDARD_PORTS])
                yield PortSelector(Selector.BLUETOOTH, ["Through TCU"])
                yield PortSelector(Selector.DEBUG, [Selector.USB, Selector.RS232])

    @on(PortSelector.PortSelected)
    def port_selected(self, event: PortSelector.PortSelected):
        event.stop()
        self.interface_ports[event.selector] = event.selection

    def get_tcu_interface(self) -> Serial | None:
        selection = self.interface_ports[Selector.TCU]

        if selection is None:
            return None

        port = Serial()
        port.port = selection
        return port

    def get_printer_interface(self, interface: Selector) -> CommsInterface | None:
        selection = self.interface_ports[interface]
        if selection is None:
            return None

        if selection in STANDARD_PORTS or selection in self._active_ports:
            port = Serial()
            port.port = selection
            return port

        if selection == "Through TCU":
            tcu_port = self.get_tcu_interface()
            if tcu_port is None:
                return None

            match interface:
                case Selector.RS232:
                    return RS232ThroughTCU(TCU(tcu_port))
                case Selector.INFRARED:
                    return IrDAThroughTCU(TCU(tcu_port))
                case Selector.BLUETOOTH:
                    return BluetoothThroughTCU(TCU(tcu_port))
                case _:
                    pass

        raise Exception(f"Unexpected {interface} interface selected: {selection}")

    def get_debug_interface(self) -> CommsInterface | None:
        interface = self.interface_ports[Selector.DEBUG]
        if interface is None:
            return None

        return self.get_printer_interface(Selector(interface))

    def _get_active_ports(self) -> list[str]:
        return [p.name for p in serial.tools.list_ports.comports()]
