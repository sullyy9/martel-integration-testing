from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from robot.api import Failure, ContinuableFailure, SkipExecution
from robot.api.deco import keyword, library
from robot.libraries.BuiltIn import BuiltIn, register_run_keyword

import cv2 as cv

from martel_print_mech_analyser import PrintMechAnalyser, Printout
from . import setup
from . import printout_matching as pm


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

        self._mech_analyser.export_printout(filepath)

    @keyword('Clear Printout')
    def clear_printout(self) -> None:
        if not self._mech_analyser:
            raise SkipExecution('Skipping tests requiring print analysis.')

        self._mech_analyser.clear()

    @keyword('Printout Should Match Exactly')
    def printout_should_match(self, sample: Printout) -> None:
        printout: Printout = self.get_printout()

        similarity: float = pm.printout_similarity(printout, sample)

        if similarity != 1.0:
            append_comparison_to_test_log(printout, sample)

            percent = similarity * 100
            raise Failure(
                f'Printout only matches the sample by {percent:.4f}%')


register_run_keyword(PrintoutCaptureLibrary,
                     'Run Keywords And Capture Printout',
                     deprecation_warning=False)


def append_comparison_to_test_log(printout: Printout, sample: Printout) -> None:
    outdir: Path = Path(BuiltIn().get_variable_value("${OUTPUT DIR}"))

    comparison_path: Path = Path(outdir, 'comparison')
    comparison_path.mkdir(exist_ok=True)

    filename = BuiltIn().get_variable_value("${TEST NAME}") + '.png'
    filepath = Path(comparison_path, filename)

    comparison = pm.create_comparison(
        sample,
        printout,
        annotation_old='Sample',
        annotation_new='Printout'
    )

    cv.imwrite(str(filepath.absolute()), comparison)

    # Append the iamge to the Robot Framework test report.
    BuiltIn().set_test_message("\n", append=True)
    BuiltIn().set_test_message(
        f"*HTML* <img src='{filepath.relative_to(outdir)}' width='100%'/>",
        append=True
    )
