import serial.tools.list_ports

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Placeholder, Select, Label


class PortSelector(Container):
    def __init__(self, name: str) -> None:
        super().__init__()

        ports = serial.tools.list_ports.comports()
        self._options = [(str(p), p.name) for p in ports]
        self._name: str = name

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self._name)
            yield Select(self._options)


class PortSelection(Container):
    def compose(self) -> ComposeResult:
        yield PortSelector("TCU Port")
        yield PortSelector("USB Port")
