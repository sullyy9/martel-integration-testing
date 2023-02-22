from datetime import timedelta
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Optional

from robot.api import Failure, ContinuableFailure, SkipExecution
from robot.api.deco import keyword, library
from robot.libraries.BuiltIn import BuiltIn, register_run_keyword

from martel_print_mech_analyser import PrintMechAnalyser, Printout

from . import setup


class TextSequence(Enum):
    FULL_CHARACTER_SET = [i for i in range(0, 256)]


@library(scope='GLOBAL')
class PrintoutCaptureLibrary:
    def __init__(self, output_directory: Optional[Path] = None) -> None:
        self._mech_analyser: Optional[PrintMechAnalyser]
        self._outdir: Optional[Path] = output_directory

    @keyword('Setup Printout Capture Library')
    def setup(self) -> None:
        self._mech_analyser = setup.from_user_get_mech_analyser()

    @keyword('Run Keywords And Capture Printout')
    def run_keywords_and_capture(self,
                                 *keywords,
                                 timeout: timedelta = timedelta(seconds=10)
                                 ) -> None:
        if not self._mech_analyser:
            raise SkipExecution('Skipping tests requiring print analysis.')

        self._mech_analyser.start_capture()

        if 'AND' not in keywords:
            BuiltIn().run_keyword(*keywords)
        else:
            BuiltIn().run_keywords(*keywords)

        try:
            self._mech_analyser.await_capture_completion(timeout)
        except TimeoutError:
            raise ContinuableFailure(
                f'No printout was captured within the timeframe ({timeout}).'
            )

    @keyword('Get Printout')
    def get_printout(self) -> Printout:
        if not self._mech_analyser:
            raise SkipExecution('Skipping tests requiring print analysis.')

        printout = self._mech_analyser.get_printout()
        if printout is None:
            raise Failure('No recorded printout.')

        return printout

    @keyword('Save Printout')
    def save_printout(self, filepath: Path) -> None:
        if not self._mech_analyser:
            raise SkipExecution('Skipping tests requiring print analysis.')

        printout = self._mech_analyser.get_printout()
        if printout is None:
            raise Failure('No recorded printout.')

        printout.save(filepath)

    @keyword('Clear Printout')
    def clear_printout(self) -> None:
        if not self._mech_analyser:
            raise SkipExecution('Skipping tests requiring print analysis.')

        self._mech_analyser.clear()


register_run_keyword(PrintoutCaptureLibrary,
                     'Run Keywords And Capture Printout')
