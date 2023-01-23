import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import cv2

import numpy as np
from numpy import uint8, float64
from numpy.typing import NDArray

from .printout import Printout
from .signal_analyser import SampleRecord

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

class PrintMechEmulator:
    """
    Simulation of the current state of the printer's print mechanism.

    """

    __slots__ = ('_last_input', '_shift_register', '_latch_register',
                 '_burn_time', '_motor_steps', '_paper_buffer')

    def __init__(self, initial_state: np.record) -> None:
        
        self._shift_register: NDArray[uint8] = np.zeros(DOTS_PER_LINE, uint8)
        self._latch_register: NDArray[uint8] = np.zeros(DOTS_PER_LINE, uint8)
        self._last_input: np.record = initial_state

        self._paper_buffer: NDArray[float64] = np.zeros([2, DOTS_PER_LINE])

        self._burn_time: float = 0.0
        self._motor_steps: int = 0

    def update(self, input: np.record) -> None:
        # DST controls the activation of the thermal head
        # along with the data in the latch register
        if self._last_input['dst'] == 1:
            self._burn_time += input['timestamp'] - self._last_input['timestamp']

        # Data in the shift register is transfered to the latch
        # register when the latch is pulled low.
        if self._last_input['latch'] == 1 and input['latch'] == 0:
            self._burn_latch_register()
            self._latch_register = self._shift_register.copy()

        # Data bits are valid on the clock's rising edge.
        # The bits get shifted in to the shift register.
        if input['clock'] == 1 and self._last_input['clock'] == 0:
            self._shift_register[0:-1] = self._shift_register[1:]
            self._shift_register[-1] = input['data']

        # One dot line is 4 steps.
        motor_state = input['motor1'] + input['motor2']
        last_motor_state = self._last_input['motor1'] + self._last_input['motor2']

        if motor_state != last_motor_state:
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

        self._paper_buffer[-2, :] += burn_buffer
        if between_lines:
            self._paper_buffer[-1, :] += burn_buffer

        self._burn_time = 0.0

    def _advance_line(self) -> None:
        """
        Advance the paper by 1 dot line.

        """
        self._paper_buffer = np.vstack([self._paper_buffer, np.zeros(DOTS_PER_LINE)])

    def get_printout(self) -> Printout:
        """
        Return the image that has been burned into the paper.

        """
        self._burn_latch_register()

        self._paper_buffer *= 25000  # Make each pixel an appropriate level of grey.

        # Ensures that very faint pixels have at least the minimum grey level.
        np.ceil(self._paper_buffer, self._paper_buffer)

        # Map each element between 255 and 0 where:
        #   - 255 is white.
        #   - 0 is black.
        img: NDArray[uint8] = np.maximum(255 - self._paper_buffer, 0).astype(uint8)

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