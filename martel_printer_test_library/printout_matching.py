from pathlib import Path
from typing import Final, Optional

import numpy as np
from numpy import uint8
from numpy.typing import NDArray

import cv2 as cv

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from robot.api import Failure

from .print_mech_analyser import Printout
from .print_mech_analyser.printout import WHITE, BLACK

WHITE_BGR: Final = (255, 255, 255)
BLACK_BGR: Final = (0, 0, 0)
GREEN_BGR: Final = (0, 200, 0)
RED_BGR: Final = (0, 0, 255)


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
            comparison = create_comparison(
                sample,
                printout,
                annotation_old='Sample',
                annotation_new='Printout'
            )

            cv.imwrite(str(filepath), comparison)

            # Append the iamge to the Robot Framework test report.
            BuiltIn().set_test_message("\n", append=True)
            BuiltIn().set_test_message(
                f"*HTML* <img src='{filepath.absolute()}' width='100%'/>",
                append=True
            )


def saturate_burned_pixels(print: Printout) -> Printout:
    '''
    Make any burned pixels completely black.

    Parameters
    ----------
    print : Printout

    Returns
    -------
    Printout

    '''
    return Printout(np.where(print == WHITE, WHITE, BLACK).astype(np.uint8))


def crop_excess_length(print: Printout) -> Printout:
    '''
    Crop the excess whitespace at the top and bottom of a printout.

    Parameters
    ----------
    print : Printout

    Returns
    -------
    Printout

    '''
    row: NDArray[uint8] = np.array(np.any(print == BLACK, axis=1))
    y1, y2 = row.argmax(), row.size - row[::-1].argmax()
    return print[y1:y2]


def create_diff(old: Printout, new: Printout) -> NDArray:
    if old.width != new.width:
        raise Failure('Printouts are of differing width.')

    diff_height: int = max(old.length, new.length)

    # Make both images bicolour and crop out excess length.
    old, new = (saturate_burned_pixels(p) for p in (old, new))
    old, new = (crop_excess_length(p) for p in (old, new))

    old, new = old[:new.length], new[:old.length]

    diff = np.full((diff_height, old.width, 3), WHITE_BGR, dtype=uint8)

    # Compare pixels between the 2 printouts. Where a black pixel has been
    # added from self to other, make that pixel green in the diff. Where
    # the reverse is true, make it red in the diff.
    diff[np.where((old == BLACK) & (new == BLACK))] = BLACK_BGR
    diff[np.where((old == WHITE) & (new == BLACK))] = GREEN_BGR
    diff[np.where((old == BLACK) & (new == WHITE))] = RED_BGR
    return diff


@keyword('Load Printout')
def load_printout(filepath: str) -> Printout:
    try:
        return Printout.from_file(Path(filepath))
    except FileNotFoundError as exc:
        raise Failure(exc)


@keyword('Save Printout')
def save_printout(printout: Printout, filepath: str) -> None:
    printout.save(Path(filepath))


@keyword('Printout Similarity')
def printout_similarity(print1: Printout, print2: Printout) -> float:
    '''
    Calculate the similarity between 2 printouts. Both printouts will be
    pre-processed before hand:
        - Any burned pixels are made completely black.
        - Any excess whitespace at the top and bottom will be trimmed.

    The similarity is given as the percentage of pixels that match between the
    2 printouts.

    Parameters
    ----------
    print1 : Printout
        Printout to compare.

    print2 : Printout
        Printout to compare.

    Returns
    -------
    float
        Similarity given as the percentage of pixels that match between the
        2 printouts.

    Raises
    ------
    Failure
        If the printouts are not equal width. This implies they were produced
        by different print mechanisms and are not comparable.

    '''
    if print1.width != print2.width:
        raise Failure('Printouts are of differing width.')

    # Make both images bicolour and crop out excess length.
    print1, print2 = (saturate_burned_pixels(p) for p in (print1, print2))
    print1, print2 = (crop_excess_length(p) for p in (print1, print2))

    # Find the number of pixels that are the same where the printouts overlap.
    matching_pixels = np.sum(print1[:print2.length] == print2[:print1.length])

    # Calculate similarity as the percentage of pixels that are the same.
    # Any pixels where the printouts don't overlap are taken to be different.
    longest_length: int = max(print1.length, print2.length)
    return matching_pixels / (print1.width * longest_length)


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
    similarity: float = printout_similarity(sample, printout)

    if similarity != 1.0:
        sim_percent: float = similarity * 100
        raise Failure(f'Printout only matches the sample by {sim_percent}')


@keyword('Create Comparison')
def create_comparison(
        old: Printout,
        new: Printout,
        annotation_old: str = 'Old',
        annotation_new: str = 'New') -> NDArray[uint8]:
    """
    Create an image that details the differences between two printouts. This
    image will contain the given printouts as well as a diff image which will
    colour individual dots depending on if they were added or removed from
    'old' to 'new'.

    Parameters
    ----------
    old : Printout
        Printout to compare against.

    new : Printout
        Printout to compare against old.

    annotation_old : str
        Annotation to add above the old printout.

    annotation_new : str
        Annotation to add above the new printout.

    Returns
    -------
    NDArray[uint8]
        Comparison image.

    """
    diff = create_diff(old, new)

    old_bgr = cv.cvtColor(np.array(old), cv.COLOR_GRAY2RGB)
    new_bgr = cv.cvtColor(np.array(new), cv.COLOR_GRAY2RGB)

    # Make sure both printouts are the same length.
    if old_bgr.shape[0] < new_bgr.shape[0]:
        height_diff = new_bgr.shape[0] - old_bgr.shape[0]
        extra = np.full((height_diff, old.width, 3), WHITE_BGR)
        old_bgr = np.append(old_bgr, extra, axis=0)

    elif new_bgr.shape[0] < old_bgr.shape[0]:
        height_diff = old_bgr.shape[0] - new_bgr.shape[0]
        extra = np.full((height_diff, new.width, 3), WHITE_BGR)
        new_bgr = np.append(new_bgr, extra, axis=0)

    # Add the annotations to each image.
    border_type = cv.BORDER_CONSTANT
    old_bgr = cv.putText(
        cv.copyMakeBorder(old_bgr, 20, 0, 0, 0, border_type, value=WHITE_BGR),
        annotation_old,
        org=(0, 15),
        fontFace=cv.FONT_HERSHEY_PLAIN,
        fontScale=1,
        color=BLACK_BGR
    )
    new_bgr = cv.putText(
        cv.copyMakeBorder(new_bgr, 20, 0, 0, 0, border_type, value=WHITE_BGR),
        annotation_new,
        org=(0, 15),
        fontFace=cv.FONT_HERSHEY_PLAIN,
        fontScale=1,
        color=BLACK_BGR
    )
    diff = cv.putText(
        cv.copyMakeBorder(diff, 20, 0, 0, 0, border_type, value=WHITE_BGR),
        'Difference',
        org=(0, 15),
        fontFace=cv.FONT_HERSHEY_PLAIN,
        fontScale=1,
        color=BLACK_BGR
    )

    return np.hstack((old_bgr, new_bgr, diff)).astype(uint8)
