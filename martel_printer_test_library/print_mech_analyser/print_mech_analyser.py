from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from pathlib import Path
from typing import Final, Optional, Protocol

from .printout import Printout
from .signal_analyser import SignalAnalyser


class MechPrintError(Exception):
    pass


class MechFileError(Exception):
    pass


class MechCaptureTimeout(Exception):
    pass


@dataclass
class CaptureTask:
    execute: Final[partial]
    timeout: Final[timedelta] = timedelta(seconds=10)


class PrintMechAnalyser(Protocol):
    _analyser: SignalAnalyser

    def capture_tasks(self, tasks: list[CaptureTask]) -> None:
        '''
        Execute a series of tasks and capture the cumulative output.

        Parameters
        ----------
        tasks : list[Task]
            List of tasks to execute during the capture.

        '''
        ...

    def start_capture(self, name: Optional[str] = None) -> None:
        '''
        Start a new capture. Any captured print will be append to any existing
        print.

        '''
        ...

    def stop_capture(self) -> None:
        '''
        Stop a capture in process.

        '''
        ...

    def await_capture_completion(self, timeout: timedelta = timedelta(seconds=10)) -> None:
        '''
        Process an ongoing capture until it is complete.

        Raises
        ------
        MechCaptureTimeout
            If the capture doesn't complete within the timeout period.

        '''
        ...

    def get_printout(self) -> Optional[Printout]:
        '''
        Return the captured printout.

        Returns
        -------
        Printout
            Digital printout.

        '''
        ...

    def export_printout(self, filepath: Path) -> None:
        '''
        Export the captured printout as a PNG.

        Parameters
        ----------
        filepath : Path
            Path and name of the file to save the printout as.

        '''
        ...

    def export_raw_data(self, filepath: Path) -> None:
        '''
        Export the raw capture data as a CSV file.

        Parameters
        ----------
        filepath : Path
            Path and name of the file to save the data to.

        '''
        self._analyser.export_data(filepath)

    def clear(self) -> None:
        '''
        Clear any ongoing capture and any captured data.

        '''
        ...
