from typing import Final

from textual import on
from textual.app import ComposeResult
from textual.widgets import Select, Label
from textual.containers import Container

from martel_printer.comms import interface

from .types import Interface


class PrimarySelect(Container):
    def __init__(self, name: str, initial: Interface | None = None) -> None:
        super().__init__()

        self._label: Final = Label(name, classes="port_selector_label")
        self._select: Final = Select(
            [(p.name, p) for p in Interface],
            classes="port_selector_select",
            value=initial,
        )

    def compose(self) -> ComposeResult:
        yield self._label
        yield self._select

    @on(Select.Changed)
    def option_selected(self, event: Select.Changed) -> None:
        event.stop()
    
    def set_value(self, value: Interface | None) -> None:
        self._select.value = value

    def get_value(self) -> Interface | None:
        return self._select.value

    def lock(self) -> None:
        self._select.disabled = True

    def unlock(self) -> None:
        self._select.disabled = False
