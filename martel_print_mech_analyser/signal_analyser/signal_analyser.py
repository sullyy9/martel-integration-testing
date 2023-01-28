from datetime import timedelta
from pathlib import Path
from typing import Optional, Protocol

import numpy as np
from numpy import dtype, uint8, float32
from numpy.typing import NDArray


class DeviceError(Exception):
    pass


class CaptureTimeout(Exception):
    pass

# TODO
# Access to record elements is relatively slow. Perhaps wrap an ndarray in a
# dataclass instead?


SampleRecord = dtype([
    ('timestamp', float32),
    ('clock', uint8),
    ('data', uint8),
    ('dst', uint8),
    ('latch', uint8),
    ('motor1', uint8),
    ('motor2', uint8)
])

# TODO
# A better layout here might be to have SignalAnalyser only capable of starting
# captures but have it return an object implementing a Capture Protocol.
# The Capture protocol would allow awaiting the captures completion, stopping
# the capture, getting the data ect.


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

    def data_available_at_runtime(self) -> bool:
        '''
        Not all implementers of this protocol may be able to provide captured
        data while a capture is in progress. This maethod can be used to
        determine if a specific device can.

        Returns
        -------
        bool
            True if device can provide captured data as a capture is running.

        '''
        return False

    def take_avalable_data(self) -> Optional[NDArray[np.record]]:
        '''
        Take any available data from an ongoing capture. The taken data is
        not stored internally and will not be included in the data returned by
        get_data().

        Returns
        -------
        Optional[NDArray[np.record]]
            An array of samples and their respective timestamps. The dtype of
            the array is SampleRecord.

        Raises
        ------
        NotImplementedError
            Not all implementers of this protocol may implement this method due
            to hardware / api restrictions. See data_available_at_runtime().

        '''
        raise NotImplementedError

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
