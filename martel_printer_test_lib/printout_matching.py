from pathlib import Path
from typing import Optional

import cv2 as cv
import numpy as np

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from robot.api import Failure

from printout import Printout, BLACK_BGR


class ComparisonListener:
    """
    Robot Framework listener for generating and saving comparison images when
    printout matching keywords fail.

    """
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, comparison_directory: Optional[Path] = None):
        """
        Create a new listener.

        Parameters
        ----------
        comparison_directory : Optional[Path]
            Directory where camparison images will be saved. If none is
            specified, the deirectory will be set to ${OUTPUT DIR}/comparison.
            Where ${OUTPUT DIR} is the Robot Framework built-in varaible.

        """
        self._comparison_dir: Optional[Path] = comparison_directory

        if self._comparison_dir:
            self._comparison_dir.mkdir(exist_ok=True)

    def _get_comparison_dir(self) -> Path:
        """
        Return the path to the comparison image output directory. If it is none
        use ${OUTPUT DIR}/comparison as a default.

        Listeners are initialised before Robot Framework. Therefore the
        directory cannot be initialised with ${OUTPUT DIR} in __init__().

        """
        if self._comparison_dir:
            return self._comparison_dir
        else:
            outdir = BuiltIn().get_variable_value("${OUTPUT DIR}")
            comparison_dir = Path(outdir, 'comparison')
            comparison_dir.mkdir(exist_ok=True)
            return comparison_dir

    def end_keyword(self, name: str, attributes: dict):
        """
        Called by Robot Framework after keyword exection. Will create and save
        comparison images if a printout matching keyword fails.

        """
        matching_keyword = 'Printouts Should Match Exactly' in name
        keyword_failed = attributes['status'] == 'FAIL'

        if matching_keyword and keyword_failed:
            sample = BuiltIn().get_variable_value(attributes['args'][0])
            printout = BuiltIn().get_variable_value(attributes['args'][1])

            filename = BuiltIn().get_variable_value("${TEST NAME}") + '.png'
            filepath = Path(self._get_comparison_dir(), filename)

            create_comparison_and_save(
                sample,
                printout,
                filepath,
                add_to_test_report=True
            )


@keyword('Load Printout')
def load_printout_from_file(filepath: str) -> Printout:
    try:
        return Printout.open(Path(filepath))
    except FileNotFoundError as exc:
        raise Failure(exc)


@keyword('Printouts Should Match Exactly')
def should_match_exactly(sample: Printout, printout: Printout) -> None:
    """
    Verify that the content of the two printouts matches exactly. Each dot will
    be compared between them and must be the same. However any whitespace
    around the outside of the printout will not be taken into account.

    Parameters
    ----------
    sample : Printout
        Sample printout to compare against.

    printout : Printout
        Printout to compare against the sample.

    Raises
    ------
    Failure
        If one or more dots do not match between the two printouts.

    """
    match_percent = sample.compare_with(printout) * 100
    if match_percent != 100:
        diff_percent = 100 - match_percent
        raise Failure(
            f'Expected the printout to exactly match the sample. ' +
            f'Howver the printout does not exactly match the sample. ' +
            f'{diff_percent}% of the total dots do not match.'
        )


@keyword('Printouts Should Not Match')
def should_not_match_exactly(sample: Printout, printout: Printout) -> None:
    """
    Verify that the content of the two printouts do not match. Each dot will
    be compared between them and at least one must not be the same. However any
    whitespace around the outside of the printout will not be taken into
    account.

    Parameters
    ----------
    sample : Printout
        Sample printout to compare against.

    printout : Printout
        Printout to compare against the sample.

    Raises
    ------
    Failure
        If all of the dots match between the two printouts.

    """
    match_percent = sample.compare_with(printout) * 100
    if match_percent == 100:
        raise Failure(
            f'Expected the printout to not match the sample. ' +
            f'However the printout exactly matches the sample.'
        )


@keyword(name='Create And Save Comparison')
def create_comparison_and_save(sample: Printout,
                               printout: Printout,
                               filepath: Path,
                               add_to_test_report: bool = False) -> None:
    """
    Create an image that details the differences between two printouts. This
    image will contain the given sample and printout as well as a diff image
    which will colour individual dots depending on if they were added or
    removed from the sample to the printout.

    Parameters
    ----------
    sample : Printout
        Sample printout to compare against.

    printout : Printout
        Printout to compare against the sample.

    filepath : Printout
        Name of the image file and location to save it to. If the file already
        exists, it will be overwritten.

    add_to_test_report : bool
        If true the comparison image will be added to the report generated by
        Robot Framework, under the currently active test.

    """
    # Equilize the printout sizes.
    if sample.width < printout.width:
        sample.extend_width_to(printout.length)
    elif printout.width < sample.width:
        printout.extend_width_to(sample.width)

    if sample.length < printout.length:
        sample.extend_length_to(printout.length)
    elif printout.length < sample.length:
        printout.extend_length_to(sample.length)

    # Create the diff.
    diff = sample.create_diff_with(printout)

    # Add text to each image.
    sample_col = cv.putText(
        cv.cvtColor(sample.get_image(), cv.COLOR_GRAY2RGB),
        'Sample',
        org=(0, 15),
        fontFace=cv.FONT_HERSHEY_PLAIN,
        fontScale=1,
        color=BLACK_BGR
    )
    printout_col = cv.putText(
        cv.cvtColor(printout.get_image(), cv.COLOR_GRAY2RGB),
        'Printout',
        org=(0, 15),
        fontFace=cv.FONT_HERSHEY_PLAIN,
        fontScale=1,
        color=BLACK_BGR
    )
    diff = cv.putText(
        diff,
        'Diff',
        org=(0, 15),
        fontFace=cv.FONT_HERSHEY_PLAIN,
        fontScale=1,
        color=BLACK_BGR
    )

    # Place the images side by side and save.
    comparison = np.hstack((sample_col, printout_col, diff))

    cv.imwrite(str(filepath.absolute()), comparison)

    # Append the iamge to the Robot Framework test report.
    if add_to_test_report:
        BuiltIn().set_test_message("\n", append=True)
        BuiltIn().set_test_message(
            f"*HTML* <img src='{filepath.absolute()}' width='100%'/>",
            append=True
        )