from typing import Final
from serial import Serial
from serial.tools.list_ports_common import ListPortInfo

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical

from .tcu import TCUSelect
from .primary import PrimarySelect
from .interface import InterfaceSelect, StandardPort
from .types import Interface

from martel_printer.comms.interface import CommsInterface
from martel_tcu import TCU, RS232ThroughTCU, IrDAThroughTCU, BluetoothThroughTCU


THROUGH_TCU: Final = "TCU"


class Selectors(Container):
    def __init__(
        self,
        primary_interface: Interface | None = None,
        usb_interface: str | None = None,
        rs232_interface: str | None = None,
        infrared_interface: str | None = None,
        bluetooth_interface: str | None = None,
    ) -> None:
        super().__init__()

        self.tcu_selector: Final = TCUSelect("TCU")
        self.primary_selector: Final = PrimarySelect("Primary", primary_interface)

        self.interface_selector: Final = {
            Interface.USB: InterfaceSelect(Interface.USB, initial=usb_interface),
            Interface.RS232: InterfaceSelect(
                Interface.RS232, extra_options=[THROUGH_TCU], initial=rs232_interface
            ),
            Interface.INFRARED: InterfaceSelect(
                Interface.INFRARED,
                extra_options=[THROUGH_TCU],
                initial=infrared_interface,
            ),
            Interface.BLUETOOTH: InterfaceSelect(
                Interface.BLUETOOTH,
                extra_options=[THROUGH_TCU],
                initial=bluetooth_interface,
            ),
        }

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                yield self.tcu_selector
                yield self.primary_selector

            with Horizontal():
                yield self.interface_selector[Interface.USB]
                yield self.interface_selector[Interface.RS232]

            with Horizontal():
                yield self.interface_selector[Interface.INFRARED]
                yield self.interface_selector[Interface.BLUETOOTH]

    ##################################################

    def get_tcu_interface(self) -> Serial | None:
        value: ListPortInfo | None = self.tcu_selector.get_value()

        if value is None:
            return None

        port = Serial()
        port.port = value.name
        return port

    def get_primary_interface(self) -> CommsInterface | None:
        value: Interface | None = self.primary_selector.get_value()

        if value is None:
            return None

        return self.get_printer_interface(value)

    def get_printer_interface(self, interface: Interface) -> CommsInterface | None:
        value = self.interface_selector[interface].get_value()
        if value is None:
            return None

        if isinstance(value, (ListPortInfo, StandardPort)):
            port = Serial()
            port.port = value.name
            return port

        if value == THROUGH_TCU:
            tcu_port = self.get_tcu_interface()
            if tcu_port is None:
                return None

            match interface:
                case Interface.RS232:
                    return RS232ThroughTCU(TCU(tcu_port))
                case Interface.INFRARED:
                    return IrDAThroughTCU(TCU(tcu_port))
                case Interface.BLUETOOTH:
                    return BluetoothThroughTCU(TCU(tcu_port))
                case _:
                    pass

        raise Exception(f"Unexpected {interface} interface selected: {value}")
