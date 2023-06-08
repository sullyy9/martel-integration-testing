from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Checkbox

from robot.api import TestSuiteBuilder


class TagSelector(Container):
    def __init__(self) -> None:
        super().__init__()
        self._tags: list[str] = []

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            for tag in self._tags:
                yield Checkbox(tag)

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
