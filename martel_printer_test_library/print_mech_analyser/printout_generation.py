import csv
from dataclasses import dataclass
from pathlib import Path

import cv2

import numpy as np
from numpy import uint8, float64
from numpy.typing import NDArray

from .printout import Printout

DOTS_PER_LINE = 384


@dataclass(slots=True)
class MechInput:
    timestamp: float
    spi_clock: int
    spi_data: int
    latch: int
    dst: int
    motor_state: int


def read_mech_input(csv_path: Path):
    with open(csv_path, 'r', encoding='utf-8') as file:
        states = csv.reader(file)
        next(states, None)  # Skip the header row.

        for state in states:
            motor_al = int(state[5])
            motor_bl = int(state[6])

            yield MechInput(
                timestamp=float(state[0]),
                spi_clock=int(state[1]),
                spi_data=int(state[2]),
                latch=int(state[3]),
                dst=int(state[4]),
                motor_state=(motor_bl << 1) + (motor_al << 0)
            )


class PrintMechState:
    """
    Simulation of the current state of the printer's print mechanism.

    """

    __slots__ = ('_last_input', '_shift_register', '_latch_register', '_paper',
                 '_burn_time', '_motor_steps')

    def __init__(self, initial_state: MechInput) -> None:
        self._shift_register: NDArray[uint8] = np.zeros(DOTS_PER_LINE, uint8)
        self._latch_register: NDArray[uint8] = np.zeros(DOTS_PER_LINE, uint8)
        self._last_input: MechInput = initial_state
        self._paper: PaperBuffer = PaperBuffer()

        self._burn_time: float = 0.0
        self._motor_steps: int = 0

    def update(self, input: MechInput) -> None:
        # DST controls the activation of the thermal head
        # along with the data in the latch register
        if self._last_input.dst == 1:
            self._burn_time += input.timestamp - self._last_input.timestamp

        # Data in the shift register is transfered to the latch
        # register when the latch is pulled low.
        if self._last_input.latch == 1 and input.latch == 0:
            self._burn_latch_register()
            self._latch_register = self._shift_register.copy()

        # Data bits are valid on the clock's rising edge.
        # The bits get shifted in to the shift register.
        if input.spi_clock == 1 and self._last_input.spi_clock == 0:
            self._shift_register[0:-1] = self._shift_register[1:]
            self._shift_register[-1] = input.spi_data

        # One dot line is 4 steps.
        if input.motor_state != self._last_input.motor_state:
            self._motor_steps += 2  # 2 steps every state change
            if self._motor_steps == 2:
                self._burn_latch_register(between_lines=True)
            elif self._motor_steps >= 4:
                self._burn_latch_register()
                self._advance_line()
                self._motor_steps = 0

        self._last_input = input

    def _burn_latch_register(self, between_lines: bool = False) -> None:
        """
        Burn a dot line into the paper, simulating activation of the thermal
        head.

        """
        burn_buffer = self._latch_register * self._burn_time

        self._paper.burn_line(burn_buffer, between_lines=between_lines)
        self._burn_time = 0.0

    def _advance_line(self) -> None:
        """
        Advance the paper by 1 dot line.

        """
        self._paper.new_line()

    def get_printout(self) -> Printout:
        """
        Return the image that has been burned into the paper.

        """
        self._burn_latch_register()
        return self._paper.as_printout()


class PaperBuffer:
    """
    2D buffer representing the thermal paper.

    The paper is divided into a grid where each cell is 1 thermal head 'dot' in
    size. Each element contains the ammount of time a thermal head 'dot' has
    burned over a cell.

    """

    __slots__ = ('_buffer')

    def __init__(self) -> None:
        """
        Initialise the paper buffer with 2 lines.

        """
        self._buffer: NDArray[float64] = np.zeros([2, DOTS_PER_LINE])
        self._buffer: NDArray[float64] = np.zeros([2, DOTS_PER_LINE])

    def new_line(self) -> None:
        """
        Add a new line to the end of the buffer.

        Visualy, this line is located at the bottom of the paper.

        """
        self._buffer = np.vstack([self._buffer, np.zeros(DOTS_PER_LINE)])

    def burn_line(self,
                  line_buffer: NDArray[float64],
                  between_lines: bool = False) -> None:
        """
        Burn a line into the paper.

        This is an additive process. i.e. If the line has already been burned,
        the new line is added to the existing one. It does not replace it.

        It takes 4 motor steps to move from one line to the next. The printer
        actually moves 2 steps at once, therefore if the thermal head is
        between 2 lines, both will be burned.

        """
        self._buffer[-2, :] += line_buffer
        if between_lines:
            self._buffer[-1, :] += line_buffer

    def as_printout(self) -> Printout:
        """
        Generate a greyscale image from the buffer.

        TODO Burn time to pixel darkness could use some work.

        """
        self._buffer *= 25000  # Make each pixel an appropriate level of grey.

        # Ensures that very faint pixels have at least the minimum grey level.
        np.ceil(self._buffer, self._buffer)

        # Map each element between 255 and 0 where:
        #   - 255 is white.
        #   - 0 is black.
        img: NDArray[uint8] = np.maximum(255 - self._buffer, 0).astype(uint8)

        border = int(DOTS_PER_LINE * 0.10)
        img = cv2.copyMakeBorder(
            img,
            top=border,
            bottom=border,
            left=border,
            right=border,
            borderType=cv2.BORDER_CONSTANT,
            dst=img,  # type: ignore
            value=255
        )

        return Printout(img)
