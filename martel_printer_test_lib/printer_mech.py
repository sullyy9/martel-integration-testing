from collections import deque
from operator import add
from pathlib import Path
import csv
import math
import time
import tempfile

import cv2
import numpy
from numpy import ndarray, uint8

from analyser import Analyser
from printout import Printout

DOTS_PER_LINE = 384

""""
# => Feed paper (forward)
# <= Reverse
MOTOR_SEQUENCE = [0b1100, 0b0110, 0b0011, 0b1001]

# Find the next state of the motor moving forwards.

def next_forward(state):
    (state << 1) | (state >> (3))

# Find the next state of the motor moving backwards.


def next_backward(state):
    (state >> 1) | (state << (3))
"""


class LTPD245Emulator:

    def __init__(self):
        self.analyser = Analyser()
        self.records: list[Path] = []
        self.images: list[Path] = []

        self.outdir = tempfile.TemporaryDirectory()

    def __del__(self):
        self.end()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__del__()

    def start(self):
        if not self.analyser.is_running():
            self.analyser.start()

        self.analyser.start_print_capture()

    def end(self):
        self.analyser.end()
        self.outdir.cleanup()

    def wait_until_print_complete(self):
        self.analyser.wait_for_completion()

        record_path = Path(self.outdir.name, time.strftime(
            '%Y%m%d-%H%M%S')).with_suffix('.csv')
        self.analyser.export_capture(record_path)
        self.records.append(record_path)

        self.analyser.clear_all_captures()

    def get_last_printout(self) -> Printout:
        return self.generate_image_from_record(self.records[-1])

    def generate_image_from_record(self, record: Path) -> Printout:
        with MechInputRecords(record) as mech_record:
            print_mech = PrintMechState(next(mech_record))
            for state in mech_record:
                print_mech.update(state)

        return print_mech.get_printout()


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
    def __init__(self, csv_path: Path):
        self.file = open(csv_path, 'r', encoding='utf-8')
        self.history = csv.reader(self.file)
        next(self.history)  # Skip the header row.

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.file.close()

    def __iter__(self):
        return self

    def __next__(self) -> MechInput:
        return MechInput(next(self.history))


class PrintMechState:
    """
    Simulation of the current state of the printer's print mechanism.
    """

    def __init__(self, initial_input: MechInput):
        self.last_input = initial_input
        self.shift_register = deque([0] * DOTS_PER_LINE, maxlen=DOTS_PER_LINE)
        self.latch_register = [0] * DOTS_PER_LINE
        self.paper = PaperBuffer()

        self.burn_time = 0.0
        self.motor_steps = 0

    def update(self, mech_input: MechInput):
        # DST controls the activation of the thermal head
        # along with the data in the latch register
        if self.last_input.dst == 1:
            self.burn_time += mech_input.timestamp - self.last_input.timestamp

        # Data in the shift register is transfered to the latch
        # register when the latch is pulled low.
        if self.last_input.latch == 1 and mech_input.latch == 0:
            self.burn_shift_register()
            self.latch_register = list(self.shift_register)

        # Data bits are valid on the clock's rising edge.
        # The bits get shifted in to the shift register.
        if mech_input.spi_clock == 1 and self.last_input.spi_clock == 0:
            self.shift_register.append(mech_input.spi_data)

        # One dot line is 4 steps.
        if mech_input.motor_state != self.last_input.motor_state:
            self.motor_steps += 2  # 2 steps every state change
            if self.motor_steps == 2:
                self.burn_shift_register(between_lines=True)
            elif self.motor_steps >= 4:
                self.burn_shift_register()
                self.advance_line()
                self.motor_steps = 0

        self.last_input = mech_input

    def burn_shift_register(self, between_lines=False):
        """
        Burn a dot line into the paper, simulating activation
        of the thermal head.
        """
        burn_buffer = [
            float(bit) * self.burn_time for bit in self.latch_register]
        self.paper.burn_line(burn_buffer, between_lines=between_lines)
        self.burn_time = 0.0

    def advance_line(self):
        """
        Advance the paper by 1 dot line.
        """
        self.paper.new_line()

    def get_printout(self) -> Printout:
        """
        Return the image that has been burned into the paper.
        """
        self.burn_shift_register()
        return self.paper.as_printout()


class PaperBuffer:
    """
    2D buffer representing the thermal paper.

    The paper is divided into a grid where each cell is 1 thermal head 'dot' in size.

    Each element contains the ammount of time a thermal head 'dot' has burned over a cell.
    """

    def __init__(self):
        """
        Initialise the paper buffer with 2 lines.
        """
        self.buffer = [[0.0] * DOTS_PER_LINE, [0.0] * DOTS_PER_LINE]

    def new_line(self):
        """
        Add a new line to the end of the buffer.

        Visualy, this line is located at the bottom of the paper.
        """
        self.buffer.append([0.0] * DOTS_PER_LINE)

    def burn_line(self, line_buffer: list[float], between_lines=False):
        """
        Burn a line into the paper.

        This is an additive process. i.e. If the line has already been burned, the new
        line is added to the existing one. It does not replace it.

        It takes 4 motor steps to move from one line to the next. The printer actually moves 2
        steps at once, therefore if the thermal head is between 2 lines, both will be burned.
        """
        if not between_lines:
            self.buffer[-2] = list(map(add, self.buffer[-2], line_buffer))
        else:
            self.buffer[-2] = list(map(add, self.buffer[-2], line_buffer))
            self.buffer[-1] = list(map(add, self.buffer[-1], line_buffer))

    def as_printout(self) -> Printout:
        """
        Generate a greyscale image from the buffer.

        The method of calculating the darkness of a burned dot needs improvement.
        """
        # img = Image.new('L', (DOTS_PER_LINE, len(self.buffer)))
        # img = ndarray((len(self.buffer), DOTS_PER_LINE), dtype=uint8)
        data = [max(0, 255 - int(math.ceil(pixel * 25000.0)))
                for row in self.buffer for pixel in row]

        img = numpy.asarray(data, uint8)
        img = numpy.reshape(img, (-1, DOTS_PER_LINE))

        border = int(DOTS_PER_LINE * 0.10)
        img = cv2.copyMakeBorder(
            img,
            top=border,
            bottom=border,
            left=border,
            right=border,
            borderType=cv2.BORDER_CONSTANT,
            dst=img,
            value=255
        )

        return Printout(img)
