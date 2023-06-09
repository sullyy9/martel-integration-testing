from dataclasses import dataclass
from enum import StrEnum
import serial.tools.list_ports
from typing import Final
from serial import Serial

from textual.app import ComposeResult
from textual.widgets import Select, Label
from textual.containers import Container, Horizontal, Vertical

from martel_printer.comms.interface import CommsInterface
from martel_tcu import TCU, RS232ThroughTCU, IrDAThroughTCU, BluetoothThroughTCU


THROUGH_TCU: Final = "TCU"


class StandardPort(StrEnum):
    COM29 = "COM29"
    COM30 = "COM30"
    COM31 = "COM31"
    COM32 = "COM32"
    COM33 = "COM33"


class Interface(StrEnum):
    USB = "USB"
    RS232 = "RS232"
    INFRARED = "Infrared"
    BLUETOOTH = "Bluetooth"


def active_ports() -> list[str]:
    return [p.name for p in serial.tools.list_ports.comports()]


def com_ports() -> list[str]:
    return active_ports() + [p for p in StandardPort]


def all_ports() -> list[str]:
    return com_ports() + [THROUGH_TCU]


class Selector(Container):
    def __init__(
        self, name: str, options: list[str], init: str | None = None, lock: bool = False
    ) -> None:
        super().__init__()

        self._label: Final = Label(name, classes="port_selector_label")
        self._select: Final = Select(
            [(o, o) for o in options],
            classes="port_selector_select",
            value=init,
            disabled=lock,
        )

    def compose(self) -> ComposeResult:
        yield self._label
        yield self._select

    @property
    def value(self) -> str | None:
        return self._select.value

    @value.setter
    def value(self, value: str | None) -> None:
        self._select.value = value

    def lock(self) -> None:
        self._select.disabled = True

    def unlock(self) -> None:
        self._select.disabled = False


@dataclass
class SelectorConfig:
    primary_init: str | None = None
    usb_init: str | None = None
    rs232_init: str | None = None
    infrared_init: str | None = None
    bluetooth_init: str | None = None

    primary_lock: bool = False
    usb_lock: bool = False
    rs232_lock: bool = False
    infrared_lock: bool = False
    bluetooth_lock: bool = False


class Selectors(Container):
    def __init__(self, config: SelectorConfig = SelectorConfig()) -> None:
        super().__init__()

        self.tcu: Final = Selector("TCU", active_ports())
        self.primary: Final = Selector(
            "Primary",
            [i for i in Interface],
            init=config.primary_init,
            lock=config.primary_lock,
        )

        usb: Final = Selector(
            "USB", com_ports(), init=config.usb_init, lock=config.usb_lock
        )
        rs232: Final = Selector(
            "RS232", all_ports(), init=config.rs232_init, lock=config.rs232_lock
        )
        ir: Final = Selector(
            "Infrared",
            all_ports(),
            init=config.infrared_init,
            lock=config.infrared_lock,
        )
        bt: Final = Selector(
            "Bluetooth",
            [THROUGH_TCU],
            init=config.bluetooth_init,
            lock=config.bluetooth_lock,
        )

        self.printer: Final = {
            Interface.USB: usb,
            Interface.RS232: rs232,
            Interface.INFRARED: ir,
            Interface.BLUETOOTH: bt,
        }

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                yield self.tcu
                yield self.primary

            with Horizontal():
                yield self.printer[Interface.USB]
                yield self.printer[Interface.RS232]

            with Horizontal():
                yield self.printer[Interface.INFRARED]
                yield self.printer[Interface.BLUETOOTH]

    ##################################################

    def get_tcu_interface(self) -> Serial | None:
        value: str | None = self.tcu.value

        if value is None:
            return None

        port = Serial()
        port.port = value
        return port

    def get_primary_interface(self) -> CommsInterface | None:
        value: str | None = self.primary.value

        if value is None:
            return None

        return self.get_printer_interface(Interface(value))

    def get_printer_interface(self, interface: Interface) -> CommsInterface | None:
        value = self.printer[interface].value
        if value is None:
            return None

        if value.startswith("COM"):
            port = Serial()
            port.port = value
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
