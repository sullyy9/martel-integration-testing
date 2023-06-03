import asyncio
import contextlib
from typing import Final, Optional

from textual import on
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.message import Message
from textual.containers import Container
from textual.widgets import Header, Footer, Button, Placeholder, TextLog
from textual.worker import Worker, WorkerState

from .port_selector import PortSelection, Selector
from .runtest import TestInstance
from ..environment import TestEnvironment


class TestControls(Container):
    class StartTest(Message):
        pass

    class StopTest(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Button("Cancel Test", id="stop_test", variant="error")
        yield Button("Start Test", id="start_test", variant="success")

    @on(Button.Pressed, "#start_test")
    def start_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.post_message(self.StartTest())

    @on(Button.Pressed, "#stop_test")
    def stop_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.post_message(self.StopTest())


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
        self._test_instance: Optional[Worker] = None
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
            self._test_instance.cancel()
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
        usb = selection.get_printer_interface(Selector.USB)
        rs232 = selection.get_printer_interface(Selector.RS232)
        infrared = selection.get_printer_interface(Selector.INFRARED)
        bluetooth = selection.get_printer_interface(Selector.BLUETOOTH)
        debug = selection.get_debug_interface()

        env = TestEnvironment(
            tcu_port,
            usb,
            rs232,
            infrared,
            bluetooth,
            debug,
        )

        self._test_instance = self.run_worker(self.run_test(TestInstance(env)))

    @on(TestControls.StopTest)
    async def test_stop_requested(self) -> None:
        if self._test_instance is None:
            return

        self._test_instance.cancel()

    async def run_test(self, test: TestInstance) -> None:
        log_level: Final[str] = "DEBUG" if self._debug_mode else "INFO"

        test_run = asyncio.ensure_future(test.run(log_level))
        try:
            while not test_run.done():
                with contextlib.suppress(asyncio.TimeoutError):
                    line = await asyncio.wait_for(test.test_output.get(), 0.001)
                    self.query_one(Terminal).text = line

        except asyncio.CancelledError:
            test.kill()
            while not test_run.done():
                with contextlib.suppress(asyncio.TimeoutError):
                    line = await asyncio.wait_for(test.test_output.get(), 0.001)
                    self.query_one(Terminal).text = line

    @on(Worker.StateChanged)
    def test_complete(self) -> None:
        if self._test_instance is None:
            return

        if self._test_instance.state != WorkerState.RUNNING:
            self._test_instance = None


if __name__ == "__main__":
    app = TestRunner()
    app.run()
