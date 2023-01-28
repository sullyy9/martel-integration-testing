import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy import uint8, float32
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


class PrintMechEmulator:
    """
    Simulation of the current state of the printer's print mechanism.

    """

    __slots__ = [
        '_shift_register', '_latch_register', '_paper_buffer', '_burn_time',
        '_motor_steps',  '_last_timestamp', '_last_clock', '_last_dst',
        '_last_latch', '_last_motor_state'
    ]

    def __init__(self, initial_state: np.record) -> None:

        self._shift_register: NDArray[uint8] = np.zeros(DOTS_PER_LINE, uint8)
        self._latch_register: NDArray[uint8] = np.zeros(DOTS_PER_LINE, uint8)

        self._paper_buffer: list[NDArray[float32]] = [
            np.zeros((1, DOTS_PER_LINE), dtype=float32),
            np.zeros((1, DOTS_PER_LINE), dtype=float32)
        ]

        self._burn_time: float = 0.0
        self._motor_steps: int = 0

        self._last_timestamp: float = initial_state['timestamp']
        self._last_clock: uint8 = initial_state['clock']
        self._last_dst: uint8 = initial_state['dst']
        self._last_latch: uint8 = initial_state['latch']
        self._last_motor_state: uint8 = initial_state['motor1'] + \
            initial_state['motor2']

    def update(self, input: np.record) -> None:

        timestamp = input['timestamp']
        clock = input['clock']
        latch = input['latch']

        # DST controls the activation of the thermal head
        # along with the data in the latch register
        if self._last_dst:
            self._burn_time += timestamp - self._last_timestamp

        # Data in the shift register is transfered to the latch
        # register when the latch is pulled low.
        if self._last_latch and (not latch):
            self._burn_latch_register()
            self._latch_register = self._shift_register.copy()

        # Data bits are valid on the clock's rising edge.
        # The bits get shifted in to the shift register.
        if clock and (not self._last_clock):
            self._shift_register[:-1] = self._shift_register[1:]
            self._shift_register[-1] = input['data']

        # One dot line is 4 steps.
        motor_state = input['motor1'] + input['motor2']

        if motor_state != self._last_motor_state:
            self._motor_steps += 2  # 2 steps every state change
            if self._motor_steps == 2:
                self._burn_latch_register(between_lines=True)
            elif self._motor_steps >= 4:
                self._burn_latch_register()
                self._advance_line()
                self._motor_steps = 0

        self._last_timestamp = timestamp
        self._last_clock = clock
        self._last_dst = input['dst']
        self._last_latch = latch
        self._last_motor_state = motor_state

    def _burn_latch_register(self, between_lines: bool = False) -> None:
        """
        Burn a dot line into the paper, simulating activation of the thermal
        head.

        """
        burn_buffer = self._latch_register * self._burn_time

        self._paper_buffer[-2] += burn_buffer
        if between_lines:
            self._paper_buffer[-1] += burn_buffer

        self._burn_time = 0.0

    def _advance_line(self) -> None:
        """
        Advance the paper by 1 dot line.

        """
        self._paper_buffer.append(np.zeros(DOTS_PER_LINE, dtype=float32))

    def get_printout(self) -> Printout:
        """
        Return the image that has been burned into the paper.

        """
        self._burn_latch_register()
        paper_buffer = np.vstack(self._paper_buffer)
        paper_buffer *= 25000  # Make each pixel an appropriate level of grey.

        # Ensures that very faint pixels have at least the minimum grey level.
        np.ceil(paper_buffer, paper_buffer)

        # Map each element between 255 and 0 where:
        #   - 255 is white.
        #   - 0 is black.
        img: NDArray[uint8] = np.maximum(255 - paper_buffer, 0).astype(uint8)

        return Printout(img)
