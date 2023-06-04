import serial.tools.list_ports as list_ports
from typing import Final
from serial.tools.list_ports_common import ListPortInfo

from textual import on
from textual.app import ComposeResult
from textual.widgets import Select, Label
from textual.containers import Container


class TCUSelect(Container):
    def __init__(self, name: str, initial: ListPortInfo | None = None) -> None:
        super().__init__()

        self._label: Final = Label(name, classes="port_selector_label")
        self._select: Final = Select(
            [(p.name, p) for p in list_ports.comports()],
            classes="port_selector_select",
            value=initial,
        )

    def compose(self) -> ComposeResult:
        yield self._label
        yield self._select

    @on(Select.Changed)
    def port_selected(self, event: Select.Changed) -> None:
        event.stop()

    def set_value(self, value: ListPortInfo | None) -> None:
        self._select.value = value

    def get_value(self) -> ListPortInfo | None:
        return self._select.value

    def lock(self) -> None:
        self._select.disabled = True

    def unlock(self) -> None:
        self._select.disabled = False
