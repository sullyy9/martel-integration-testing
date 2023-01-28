
from datetime import timedelta
from pathlib import Path
from typing import Optional, Final

import numpy as np

from .printout import Printout
from .signal_analyser import SignalAnalyser, CaptureTimeout
from .print_mech_analyser import PrintMechAnalyser, CaptureTask, MechCaptureTimeout
from .printout_generation import PrintMechEmulator


class LTPD245Analyser(PrintMechAnalyser):
    """
    Analyser for the Seiko LTPD245 print mechanism.

    """
    __slots__ = ('_analyser', '_emulator')

    def __init__(self, analyser: SignalAnalyser) -> None:
        """
        Parameters
        ----------
        signal_analyser : SignalAnalyser
            Signal analyser to use to capture the raw data being sent to a
            mech.

        """
        self._analyser: Final[SignalAnalyser] = analyser
        self._emulator: Optional[PrintMechEmulator] = None

    def start_capture(self) -> None:
        self._analyser.start_capture()

    def stop_capture(self) -> None:
        self._analyser.stop_capture()

    def await_capture_completion(self, timeout=timedelta(seconds=10)) -> None:
        try:
            self._analyser.process_capture(timeout)
        except CaptureTimeout as exc:
            raise MechCaptureTimeout(
                'Print failed to complete within the given timeframe.'
            ) from exc

        # Add the captured data to the Mech emulation. Create a new one if
        # none exists.
        records = self._analyser.get_data()
        if not self._emulator:
            self._emulator = PrintMechEmulator(records[0])
            records = records[1:]

        for record in np.nditer(records):
            self._emulator.update(record)  # type: ignore

    def process_available_data(self) -> None:
        '''
        If new data is available, add it to the emulator. Otherwise do nothing.

        '''
        records = self._analyser.take_avalable_data()
        if records is None:
            return

        if not self._emulator:
            self._emulator = PrintMechEmulator(records[0])
            records = records[1:]

        for record in np.nditer(records):
            self._emulator.update(record)  # type: ignore

    def capture_tasks(self, tasks: list[CaptureTask]) -> None:
        for i, task in enumerate(tasks):
            self.start_capture()
            task.execute()

            try:
                self.await_capture_completion(timeout=task.timeout)
            except CaptureTimeout:
                raise MechCaptureTimeout(
                    f'Print task {i} capture timed out after {task.timeout.seconds}S'
                )

    def get_printout(self) -> Optional[Printout]:
        if self._emulator:
            return self._emulator.get_printout()

    def export_printout(self, filepath: Path) -> None:
        if self._emulator:
            self._emulator.get_printout().save(filepath)

    def clear(self) -> None:
        self._analyser.clear_data()
        self._emulator = None
