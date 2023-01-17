from robot.api import logger
import os
from pathlib import Path
from typing import Self

import cv2 as cv
import numpy as np
from numpy import ndarray, uint8
from numpy.typing import NDArray

WHITE = 255
BLACK = 0

WHITE_BGR = (255, 255, 255)
BLACK_BGR = (0, 0, 0)
GREEN_BGR = (0, 200, 0)
RED_BGR = (0, 0, 255)


class Printout:
    __slots__ = ('_img')

    def __init__(self, img: NDArray) -> None:
        if len(img.shape) > 2 or img.dtype != uint8:
            raise TypeError(
                'Invalid printout image format. The image must be single ',
                'channel 8bits per pixel.'
            )

        self._img: NDArray[uint8] = img

    def __del__(self) -> None:
        pass

    @classmethod
    def open(cls, filepath: Path) -> Self:
        """
        Load a printout from a file.

        Parameters
        ----------
        filepath : Path
            Path to a greyscale, 8 bits per pixel image.

        Raises
        ------
        FileNotFoundError
            If the file doesn't exist.

        """
        if not filepath.exists():
            raise FileNotFoundError(
                f'Cannot load printout from {filepath}. File does not exist.'
            )

        return cls(cv.imread(str(filepath.absolute()), cv.IMREAD_GRAYSCALE))

    def get_image(self) -> NDArray[uint8]:
        return self._img

    def save(self, path: Path):
        cv.imwrite(str(path.absolute()), self._img)

    @property
    def length(self) -> int:
        return self._img.shape[0]

    @property
    def width(self) -> int:
        return self._img.shape[1]

    @property
    def size(self) -> tuple[int, int]:
        return self._img.shape[:2]

    def extend_length_to(self, new_length: int):
        """
        Extend the length of the printout to a given length in pixels.

        Any extra space is added as whitespace to the bottom of the printout.

        """
        if self.length > new_length:
            raise ValueError(
                f'Cannot extend the length of the printout from ',
                f'{self.length} to {new_length} as it is already longer.'
            )

        padding = [(0, new_length - self.length), (0, 0)]
        self._img = np.pad(
            self._img,
            padding,
            mode='constant',
            constant_values=(WHITE, WHITE)
        )

    def extend_width_to(self, new_width: int):
        """
        Extend the width of the printout to a given length in pixels.

        Any extra space is added as whitespace to either side of the printout.

        """
        if self.width > new_width:
            raise ValueError(
                f'Cannot extend the width of the printout from {self.width} ',
                f'to {new_width} as it is already wider.'
            )

        half_pad_width: int = int((new_width - self.length) / 2)
        padding = [(0, 0), (half_pad_width, half_pad_width)]
        self._img = np.pad(
            self._img,
            padding,
            mode='constant',
            constant_values=(WHITE, WHITE)
        )

    def compare_with(self, other: Self) -> float:
        """
        Compare this printout with another and find the percentage of pixels
        that do not match. The border will be cropped from both printouts 
        and they will be converted to black and white before the comparison. 

        Parameters
        ----------
        other : Printout
            Printout to compare against.

        Returns
        -------
        float:
            Value between 0.0 to 1.0.

        """
        # Make convert both printouts to black and white. The text will be
        # white and background black as it makes it more convenient to crop.
        print1 = np.where(self._img == WHITE, BLACK, WHITE).astype(uint8)
        print2 = np.where(other._img == WHITE, BLACK, WHITE).astype(uint8)

        # Crop out the border from both images.
        row: ndarray = print1.any(axis=1)
        col: ndarray = print1.any(axis=0)
        y1, y2 = row.argmax(), row.size - row[::-1].argmax()
        x1, x2 = row.argmax(), col.size - col[::-1].argmax()
        print1 = print1[y1:y2, x1:x2]

        row: ndarray = print2.any(axis=1)
        col: ndarray = print2.any(axis=0)
        y1, y2 = row.argmax(), row.size - row[::-1].argmax()
        x1, x2 = row.argmax(), col.size - col[::-1].argmax()
        print2 = print2[y1:y2, x1:x2]

        # Calculate the difference.
        pixels_different = np.sum(print1 != print2)
        similarity = 1 - (pixels_different / (self.width * self.length))
        return similarity

    def create_diff_with(self, other: Self) -> NDArray[uint8]:
        """
        Create an image highlighting the differences between this and another
        printout. Where a black pixel has been added from this to the other,
        the same pixel in the diff image will be green. Where the reverse is
        true, it will be red.

        Parameters
        ----------
        other : Printout
            Must be the same size as self.

        Returns
        -------
        NDArray[uint8]
            Diff image.

        """
        if self.size != other.size:
            raise ValueError(
                f'Cannot create diff for printouts that are not the same ',
                f'size. {os.linesep}',
                f'This size: {self.size} {os.linesep}',
                f'Other size: {other.size} {os.linesep}',
            )

        # Convert to black and white.
        print1 = np.where(self._img == WHITE, WHITE, BLACK).astype(uint8)
        print2 = np.where(other._img == WHITE, WHITE, BLACK).astype(uint8)

        shape = [print1.shape[0], print1.shape[1], 3]
        diff = np.full(shape, WHITE_BGR, dtype=uint8)

        # Compare pixels between the 2 printouts. Where a black pixel has been
        # added from self to other, make that pixel green in the diff. Where
        # the reverse is true, make it red in the diff.
        diff[np.where((print1 == BLACK) & (print2 == BLACK))] = BLACK_BGR
        diff[np.where((print1 == WHITE) & (print2 == BLACK))] = GREEN_BGR
        diff[np.where((print1 == BLACK) & (print2 == WHITE))] = RED_BGR
        return diff
