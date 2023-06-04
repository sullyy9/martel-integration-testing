from enum import StrEnum
import serial.tools.list_ports
from typing import Final, Optional
from serial.tools.list_ports_common import ListPortInfo

from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.containers import Container
from textual.widgets import Select, Label


class StandardPort(StrEnum):
    COM29 = "COM29"
    COM30 = "COM30"
    COM31 = "COM31"
    COM32 = "COM32"


# Allow any active or standard port.
class InterfaceSelect(Container):
    def __init__(
        self,
        name: str,
        extra_options: Optional[list[str]] = None,
        initial: ListPortInfo | StandardPort | str | None = None,
    ) -> None:
        super().__init__()

        options: Final = [
            *[(p.name, p) for p in serial.tools.list_ports.comports()],
            *[(p.value, p) for p in StandardPort],
        ]

        if extra_options is not None:
            options.extend([(o, o) for o in extra_options])

        self._label: Final = Label(name, classes="port_selector_label")
        self._select: Final = Select(
            options, classes="port_selector_select", value=initial
        )

    def compose(self) -> ComposeResult:
        yield self._label
        yield self._select

    @on(Select.Changed)
    def port_selected(self, event: Select.Changed) -> None:
        event.stop()

    def set_value(self, value: ListPortInfo | StandardPort | str | None) -> None:
        self._select.value = value

    def get_value(self) -> ListPortInfo | StandardPort | str | None:
        return self._select.value

    def lock(self) -> None:
        self._select.disabled = True

    def unlock(self) -> None:
        self._select.disabled = False
