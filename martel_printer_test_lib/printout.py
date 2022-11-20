import os
import itertools
from pathlib import Path

import cv2
import numpy
from numpy import ndarray, uint8

from robot.api.deco import keyword, library
from robot.libraries.BuiltIn import BuiltIn
from robot.api import Failure

WHITE_GS = 255
BLACK_GS = 0

WHITE_BGR = (255, 255, 255)
BLACK_BGR = (0, 0, 0)
GREEN_BGR = (0, 200, 0)
RED_BGR = (0, 0, 255)


# Exceptions
class InvalidFormat(Exception):
    pass


class SampleNotSet(Exception):
    pass


class CannotLoadSample(Exception):
    pass


class FormatError(Exception):
    pass


class SizeError(Exception):
    pass


class Printout:
    def __init__(self, img: ndarray):
        if len(img.shape) > 2 or img.dtype != uint8:
            raise FormatError('Printout must be single channel 8bpp format.')

        self.img = img

    def __del__(self):
        pass

    def __iter__(self) -> 'PrintoutLinesIter':
        return PrintoutLinesIter(self.img)

    @classmethod
    def open(cls, filepath: Path) -> 'Printout':
        if not filepath.exists():
            raise FileNotFoundError(f'Cannot find file {filepath}')

        return cls(cv2.imread(str(filepath.absolute()), cv2.IMREAD_GRAYSCALE))

    def get_image(self) -> ndarray:
        return self.img

    def save(self, path: Path):
        cv2.imwrite(str(path.absolute()), self.img)

    @property
    def length(self) -> int:
        return self.img.shape[0]

    @property
    def width(self) -> int:
        return self.img.shape[1]

    @property
    def size(self) -> tuple[int, int]:
        return self.img.shape[:2]

    def extend_length_to(self, new_length: int):
        """
        Extend the length of the printout to a given length in pixels.

        Any extra space is added as whitespace to the bottom of the printout.
        """
        if self.length > new_length:
            raise SizeError(
                'Cannot extend printout as it is already longer than the given length.',
                'printout length: ', self.length)

        tmp = ndarray((new_length, self.img.shape[1]), dtype=self.img.dtype)
        tmp[:self.img.shape[0], :] = self.img
        tmp[self.img.shape[0]:, :] = WHITE_GS
        self.img = tmp

    def extend_width_to(self, new_width: int):
        """
        Extend the width of the printout to a given length in pixels.

        Any extra space is added as whitespace to either side of the printout.
        """
        if self.width > new_width:
            raise SizeError(
                'Cannot widen printout as it is already wider than the given width.',
                'printout length: ', self.width)

        tmp = ndarray((self.length, new_width), dtype=self.img.dtype)

        # Horizontal start and end position of self within the new image.
        self_start = int((new_width - self.width) / 2)
        self_end = int(self_start + self.width)

        tmp[:, :self_start] = WHITE_GS
        tmp[:, self_start:self_end] = self.img
        tmp[:, self_end:] = WHITE_GS
        self.img = tmp

    def compare_with(self, other: 'Printout') -> float:
        """
        Find the percentage by which the images match.

        Returns
        -------
        Float - Value between 0.0 to 1.0.

        Exceptions
        ----------
        - Raises SizeError if the prinouts are not the same size.
        """
        # Crop both images.
        # Make pure white pixels black, make grey and black pixels white.
        (_, print1) = cv2.threshold(self.img, 254, WHITE_GS, cv2.THRESH_BINARY_INV)
        x, y, w, h = cv2.boundingRect(print1)
        print1 = self.img[y:y+h, x:x+w]

        (_, print2) = cv2.threshold(other.img,
                                    254, WHITE_GS, cv2.THRESH_BINARY_INV)
        x, y, w, h = cv2.boundingRect(print2)
        print2 = other.img[y:y+h, x:x+w]

        if print1.shape != print2.shape:
            raise SizeError(
                'Cannot compare printouts that are not the same size.',
                'This size: ', print1.shape,
                'Other size: ', print2.shape
            )

        # Convert all gray pixels to black.
        (_, print1) = cv2.threshold(print1, 254, WHITE_GS, cv2.THRESH_BINARY)
        (_, print2) = cv2.threshold(print2, 254, WHITE_GS, cv2.THRESH_BINARY)

        pixels_different = numpy.sum(print1 != print2)
        similarity = 1 - (pixels_different / (self.width * self.length))

        return similarity

    def create_diff_with(self, other: 'Printout') -> cv2.Mat:
        """
        """
        if self.img.shape != other.img.shape:
            raise SizeError(
                'Cannot create diff for printouts that are not the same size.',
                'This size: ', self.img.shape,
                'Other size: ', other.img.shape
            )

        # Convert all gray pixels to black.
        (_, print1) = cv2.threshold(self.img, 254, WHITE_GS, cv2.THRESH_BINARY)
        (_, print2) = cv2.threshold(other.img, 254, WHITE_GS, cv2.THRESH_BINARY)
        black, white = 0, 255

        # Compare pixels between the 2 inputs.
        # If it has been added, make it green in the diff.
        # If removed, make it red in the diff.
        diff = numpy.full((self.length, self.width, 3), WHITE_BGR, dtype=uint8)
        diff_width = diff.shape[1]
        diff_height = diff.shape[0]
        for pos in itertools.product(range(0, diff_height-1), range(0, diff_width-1)):
            if print1[pos] == WHITE_GS and print2[pos] == BLACK_GS:
                diff[pos] = GREEN_BGR
            elif print1[pos] == BLACK_GS and print2[pos] == WHITE_GS:
                diff[pos] = RED_BGR
            elif print1[pos] == BLACK_GS and print2[pos] == BLACK_GS:
                diff[pos] = BLACK_BGR
            else:
                pass  # White

        return diff


class PrintoutLinesIter:
    def __init__(self, img: ndarray):
        if len(img.shape) > 2 or img.dtype != uint8:
            raise FormatError('Printout must be single channel 8bpp format.')

        self.img = img
        self.row = 0
        self.max_row = img.shape[0] - 1

    def __next__(self) -> cv2.Mat:
        # Find the start of the text line.
        while numpy.all(self.img[self.row] == WHITE_GS):
            self.row += 1
            if self.row > self.max_row:
                raise StopIteration

        # Copy the text row into a new image.
        text_row = []
        while not numpy.all(self.img[self.row] == WHITE_GS):
            text_row.append(self.img[self.row])
            self.row += 1
            if self.row > self.max_row:
                raise StopIteration

        return numpy.asarray(text_row)


@library(scope='GLOBAL')
class ComparisonLibrary:
    COMPARISON_DIR = 'comparison'
    SAMPLE_DIR = 'samples'

    def __init__(self):
        self.sample = None

        self.output_path = Path(os.getcwd(), 'output').absolute()
        self.comparison_path = Path(self.output_path, self.COMPARISON_DIR)
        self.sample_path = Path(os.getcwd(), self.SAMPLE_DIR)

    @keyword('Create Comparison Library Output Directories')
    def create_output_directories(self):
        """
        Create output directories for printout and comparison images.

        These directories will be created in the directory specified by the
        ${OUTPUT DIR} global variable in Robot Framework.

        """
        self.output_path = Path(
            BuiltIn().get_variable_value("${OUTPUT DIR}")).absolute()

        self.compare_path = Path(self.output_path, self.COMPARISON_DIR)
        self.sample_path = Path(os.getcwd(), self.SAMPLE_DIR)

        os.makedirs(self.compare_path, exist_ok=True)

    @keyword('Load Sample "${filename}"')
    def load_sample(self, filename: str):
        try:
            self.sample = Printout.open(Path(self.sample_path, filename))
        except FileNotFoundError as exc:
            raise Failure(f'Failed to load sample - {exc}')
        except FormatError as exc:
            raise Failure('Sample has incorrect format') from exc
        except:
            raise Failure('Unknown error when loading sample')

    @keyword('Clear Sample')
    def clear_sample(self):
        self.sample = None

    @keyword('Get Sample')
    def get_sample(self) -> Printout | None:
        if self.sample is None:
            raise SampleNotSet
        return self.sample

    @keyword('Sample Should Match "${printout}"')
    def matches(self, printout: Printout):
        if self.sample is None:
            raise SampleNotSet(
                'No sample has been set to compare a printout against'
            )

        try:
            if self.sample.compare_with(printout) != 1.0:
                raise Failure('Printout content does not match sample')
        except SizeError as exc:
            raise Failure('Printout size does not match sample.') from exc

    @keyword(name='Save Comparison')
    def create_comparison_and_save(self, printout: Printout, filename: str):
        if self.sample is None:
            raise Failure('No Sample Set')

        # Equilize the printout sizes.
        if self.sample.width < printout.width:
            self.sample.extend_width_to(printout.length)
        if printout.width < self.sample.width:
            printout.extend_width_to(self.sample.width)

        if self.sample.length < printout.length:
            self.sample.extend_length_to(printout.length)
        if printout.length < self.sample.length:
            printout.extend_length_to(self.sample.length)
        print_width = self.sample.width

        diff_image = self.sample.create_diff_with(printout)

        # Create the comparison image which contains the sample, printout and diff
        # side by side.
        shape = (self.sample.length, print_width * 3, 3)
        comparison_img = numpy.full(shape, WHITE_BGR, dtype=uint8)

        comparison_img[:, :print_width] = cv2.cvtColor(
            self.sample.get_image(), cv2.COLOR_GRAY2RGB)
        comparison_img[:, print_width:(
            print_width * 2)] = cv2.cvtColor(printout.get_image(), cv2.COLOR_GRAY2RGB)
        comparison_img[:, (print_width * 2):] = diff_image

        # Label the images.
        comparison_img = cv2.putText(
            comparison_img, 'Sample',
            org=(0, 15),
            fontFace=cv2.FONT_HERSHEY_PLAIN,
            fontScale=1,
            color=(0, 0, 0)
        )
        comparison_img = cv2.putText(
            comparison_img, 'Printout',
            org=(print_width, 15),
            fontFace=cv2.FONT_HERSHEY_PLAIN,
            fontScale=1,
            color=(0, 0, 0)
        )
        comparison_img = cv2.putText(
            comparison_img, 'Diff',
            org=(print_width * 2, 15),
            fontFace=cv2.FONT_HERSHEY_PLAIN,
            fontScale=1,
            color=(0, 0, 0)
        )

        cv2.imwrite(str(Path(self.compare_path, filename)), comparison_img)

        BuiltIn().set_test_message("\n", append=True)
        img_path = Path(self.COMPARISON_DIR, filename)
        BuiltIn().set_test_message(
            f"*HTML* <img src='{img_path}' width='100%'/>",
            append=True
        )
