from pathlib import Path
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Checkbox, Button

from robot.api import TestSuiteBuilder


class TagSelector(Container):
    def __init__(self) -> None:
        super().__init__()
        self._tags: list[str] = []

    def compose(self) -> ComposeResult:
        yield Button("All", id="select_all")
        yield Button("None", id="select_none")
        with VerticalScroll(id="tag_selector_scroll"):
            for tag in self._tags:
                yield Checkbox(tag)

    @on(Button.Pressed, "#select_all")
    def start_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        for check in self.query(Checkbox):
            check.value = True

    @on(Button.Pressed, "#select_none")
    def stop_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        for check in self.query(Checkbox):
            check.value = False

    def update_tags(self, testsuite: Path) -> None:
        self._tags.clear()

        for test in TestSuiteBuilder().build(testsuite).all_tests:
            self._tags.extend(test.tags)

        self._tags = list(dict.fromkeys((self._tags)))
        self._tags.sort()

    def get_selected_tags(self) -> list[str]:
        tags: list[str] = []
        for check in self.query(Checkbox):
            if check.value:
                tags.append(str(check.label))

        return tags
