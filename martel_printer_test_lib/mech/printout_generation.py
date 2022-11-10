import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import cv2

import numpy as np
from numpy import uint8, float64
from numpy.typing import NDArray

from printout import Printout

DOTS_PER_LINE = 384

@dataclass
class MechInput:
    def __init__(self, state: list[str]):
        self.timestamp = float(state[0])
        self.spi_clock = int(state[1])
        self.spi_data = int(state[2])
        self.latch = int(state[3])
        self.dst = int(state[4])

        motor_al = int(state[5])
        motor_bl = int(state[6])
        self.motor_state = (motor_bl << 1) + (motor_al << 0)


class MechInputRecords:
    def __init__(self, csv_path: Path) -> None:
        self.file = open(csv_path, 'r', encoding='utf-8')
        self.history = csv.reader(self.file)
        next(self.history)  # Skip the header row.

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.file.close()

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> MechInput:
        return MechInput(next(self.history))


class PrintMechState:
    """
    Simulation of the current state of the printer's print mechanism.

    """
    def __init__(self, initial_input: MechInput) -> None:
        self.last_input: MechInput = initial_input
        self.shift_register: NDArray[uint8] = np.zeros(DOTS_PER_LINE, uint8)
        self.latch_register: NDArray[uint8] = np.zeros(DOTS_PER_LINE, uint8)
        self.paper: PaperBuffer = PaperBuffer()

        self.burn_time: float = 0.0
        self.motor_steps: int = 0

    def update(self, mech_input: MechInput) -> None:
        # DST controls the activation of the thermal head
        # along with the data in the latch register
        if self.last_input.dst == 1:
            self.burn_time += mech_input.timestamp - self.last_input.timestamp

        # Data in the shift register is transfered to the latch
        # register when the latch is pulled low.
        if self.last_input.latch == 1 and mech_input.latch == 0:
            self.burn_latch_register()
            self.latch_register = self.shift_register.copy()

        # Data bits are valid on the clock's rising edge.
        # The bits get shifted in to the shift register.
        if mech_input.spi_clock == 1 and self.last_input.spi_clock == 0:
            self.shift_register[0:-1] = self.shift_register[1:]
            self.shift_register[-1] = mech_input.spi_data

        # One dot line is 4 steps.
        if mech_input.motor_state != self.last_input.motor_state:
            self.motor_steps += 2  # 2 steps every state change
            if self.motor_steps == 2:
                self.burn_latch_register(between_lines=True)
            elif self.motor_steps >= 4:
                self.burn_latch_register()
                self.advance_line()
                self.motor_steps = 0

        self.last_input = mech_input

    def burn_latch_register(self, between_lines: bool = False) -> None:
        """
        Burn a dot line into the paper, simulating activation of the thermal
        head.

        """
        burn_buffer = self.latch_register * self.burn_time

        self.paper.burn_line(burn_buffer, between_lines=between_lines)
        self.burn_time = 0.0

    def advance_line(self) -> None:
        """
        Advance the paper by 1 dot line.

        """
        self.paper.new_line()

    def get_printout(self) -> Printout:
        """
        Return the image that has been burned into the paper.

        """
        self.burn_latch_register()
        return self.paper.as_printout()


class PaperBuffer:
    """
    2D buffer representing the thermal paper.

    The paper is divided into a grid where each cell is 1 thermal head 'dot' in
    size. Each element contains the ammount of time a thermal head 'dot' has
    burned over a cell.

    """

    def __init__(self) -> None:
        """
        Initialise the paper buffer with 2 lines.

        """
        self.buffer: NDArray[float64] = np.zeros([2, DOTS_PER_LINE])

    def new_line(self) -> None:
        """
        Add a new line to the end of the buffer.

        Visualy, this line is located at the bottom of the paper.

        """
        self.buffer = np.vstack([self.buffer, np.zeros(DOTS_PER_LINE)])

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
        if between_lines:
            self.buffer[-2, :] += line_buffer
            self.buffer[-1, :] += line_buffer
        else:
            self.buffer[-2, :] += line_buffer

    def as_printout(self) -> Printout:
        """
        Generate a greyscale image from the buffer.

        TODO Burn time to pixel darkness could use some work.

        """
        self.buffer = np.ceil((self.buffer * 2500000.0))

        # Map each element between 255 and 0 where:
        #   - 255 is white.
        #   - 0 is black.
        img: NDArray[uint8] = np.maximum(255 - self.buffer, 0).astype(uint8)

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
