from datetime import timedelta
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy import dtype, uint8, float64
from numpy.typing import NDArray


class DeviceError(Exception):
    pass


class CaptureTimeout(Exception):
    pass


SampleRecord = dtype([
    ('timestamp', float64),
    ('clock', uint8),
    ('data', uint8),
    ('dst', uint8),
    ('latch', uint8),
    ('motor1', uint8),
    ('motor2', uint8)
])


class SignalAnalyser(Protocol):
    '''
    Protocol for logic analysers that can be used to capture print mech signals.

    '''

    def start_capture(self) -> None:
        '''
        Start a new capture. Samples collected during this capture will
        appended to any existing samples.

        '''
        ...

    def stop_capture(self) -> None:
        '''
        Stop an ongoing capture. If no capture is running, this has no effect.

        '''
        ...

    def process_capture(self, timeout: timedelta = timedelta(seconds=10)) -> None:
        '''
        Process an ongoing capture. Some implementations of this protocol may
        require a capture to be processed while running. In these instances,
        it is recomended to call this directly after starting a capture to
        ensure no samples are lost.

        '''
        ...

    def get_data(self) -> NDArray[np.record]:
        '''
        Return captured samples and their respective timestamps.

        Returns
        -------
        NDArray[np.record]
            An array of samples and their respective timestamps. The dtype of
            the array is SampleRecord.

        '''
        ...

    def export_data(self, filepath: Path) -> None:
        '''
        Export captured samples and their respective timestamps in csv format.

        Parameters
        ----------
        filepath : Path
            Path to and name of the exported file. 

        '''
        ...

    def clear_data(self) -> None:
        '''
        Clear any captured samples and their respective timestamps.

        '''
        ...
