from typing import Final, Optional

from textual import on
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.message import Message
from textual.containers import Container
from textual.widgets import Header, Footer, Button, Placeholder, TextLog

from .port_selector import PortSelection
from .runtest import TestInstance
from ..environment import TestEnvironment, PrinterInterface


class TestControls(Container):
    class StartTest(Message):
        pass

    class TestStartButton(Button):
        pass

    class TestStopButton(Button):
        pass

    def compose(self) -> ComposeResult:
        yield self.TestStopButton("Cancel Test", variant="error")
        yield self.TestStartButton("Start Test", variant="success")

    @on(TestStartButton.Pressed)
    def start_button_pressed(self, event: TestStartButton.Pressed) -> None:
        event.stop()
        self.post_message(self.StartTest())


class Terminal(Container):
    text: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield TextLog(id="terminal")

    def watch_text(self) -> None:
        self.query_one(TextLog).write(self.text)

    def clear(self) -> None:
        self.query_one(TextLog).clear()


class TestRunner(App):
    CSS_PATH = "test_runner.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("x", "toggle_debug", "Toggle debug mode"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._test_instance: Optional[TestInstance] = None
        self._debug_mode: bool = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Placeholder("Tabs", id="tabs")
        yield PortSelection()
        yield Placeholder("Tag Selection", id="tag_selection")
        yield Terminal(id="terminal_area")
        yield Footer()

        yield TestControls(id="test_controls_area")

    def action_quit(self) -> None:
        if self._test_instance is not None:
            self._test_instance.kill()
        self.exit()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_toggle_debug(self) -> None:
        self._debug_mode = not self._debug_mode

    @on(TestControls.StartTest)
    async def test_start_requested(self) -> None:
        if self._test_instance is not None:
            return

        self.query_one(Terminal).clear()

        # Set the test environment.
        selection = self.query_one(PortSelection)

        tcu_port = selection.get_tcu_interface()
        usb = selection.get_printer_interface(PrinterInterface.USB)
        rs232 = selection.get_printer_interface(PrinterInterface.RS232)
        infrared = selection.get_printer_interface(PrinterInterface.INFRARED)
        bluetooth = selection.get_printer_interface(PrinterInterface.BLUETOOTH)
        debug = selection.get_debug_interface()

        env = TestEnvironment(
            tcu_port,
            usb,
            rs232,
            infrared,
            bluetooth,
            debug,
        )

        self._test_instance = TestInstance(env)

        log_level: Final[str] = "DEBUG" if self._debug_mode else "INFO"
        await self._test_instance.start(log_level)

        async for line in self._test_instance.output():
            self.query_one(Terminal).text = line

        self._test_instance = None


if __name__ == "__main__":
    app = TestRunner()
    app.run()
