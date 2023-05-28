from asyncio.subprocess import Process
import contextlib
import asyncio
from typing import Optional

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.message import Message
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button, Placeholder, TextLog, Select
from textual import on

from .port_selector import PortSelection


class TestControls(Container):
    class StartTest(Message):
        pass

    class TestStartButton(Button):
        pass

    def compose(self) -> ComposeResult:
        yield self.TestStartButton("Start test", variant="success")

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


class TestRunner(App):
    CSS_PATH = "test_runner.css"
    BINDINGS = [("q", "quit", "Quit"), ("d", "toggle_dark", "Toggle dark mode")]

    def __init__(self) -> None:
        super().__init__()
        self._test_process: Optional[Process] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Placeholder("Tabs", id="tabs")
        yield PortSelection(id="port_selection")
        yield Placeholder("Tag Selection", id="tag_selection")
        yield Terminal(id="terminal_area")

        yield TestControls(id="test_controls_area")

    def action_quit(self) -> None:
        if self._test_process is not None:
            self._test_process.kill()
        self.exit()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    @on(TestControls.StartTest)
    async def test_start_requested(self) -> None:
        """Event handler called when a button is pressed."""

        if self._test_process is None:
            self._test_process = await asyncio.create_subprocess_exec(
                "poetry",
                "run",
                "robot",
                "--consolecolors",
                "ANSI",
                "--outputdir",
                "./output_testsuite_pcb",
                "--pythonpath",
                "./martel_test_library",
                "./testsuite_pcb",
                stdout=asyncio.subprocess.PIPE,
            )

            stdout: Optional[asyncio.StreamReader] = self._test_process.stdout
            if stdout is None:
                await self._test_process.wait()
                return

            file = open("test_out", mode="wb")

            while await self._test_is_running():
                with contextlib.suppress(asyncio.TimeoutError):
                    line: bytes = await asyncio.wait_for(stdout.readline(), 0.1)
                    self.query_one(Terminal).text = line.decode().removesuffix("\n")

            self._test_process = None

    async def _test_is_running(self) -> bool:
        if self._test_process is None:
            return False

        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(self._test_process.wait(), 1e-6)
        return self._test_process.returncode is None


if __name__ == "__main__":
    app = TestRunner()
    app.run()
