import csv
import weakref
from datetime import timedelta, datetime
from pathlib import Path
from weakref import finalize
from typing import Final, Optional, Tuple

import numpy as np
from numpy import uint8, uint32, float64
from numpy.typing import NDArray
import numpy.core.records as nprec

import pydwf
import pydwf.utilities
from pydwf.core.dwf_device import DwfDevice, DigitalIn, DigitalOut
from pydwf import DwfEnumConfigInfo, DwfState, DwfAcquisitionMode, DwfDigitalInSampleMode
from pydwf import DwfTriggerSource, DwfTriggerSlope
from pydwf import DwfDigitalOutType, DwfDigitalOutIdle
from pydwf import PyDwfError, DwfLibraryError

from .signal_analyser import SampleRecord, SignalAnalyser, DeviceError, CaptureTimeout

dwf: Final = pydwf.DwfLibrary()


def maximize_digital_in_buffer_size(config_parameters):
    return config_parameters[DwfEnumConfigInfo.DigitalInBufferSize]


# Din pins to sample.
channels: Final[dict] = {
    'clk': 0,
    'dat': 1,
    'dst': 2,
    'lat': 3,
    'mtr1': 4,
    'mtr2': 5,

    'count0': 8,
    'count1': 9,
    'count2': 10,
    'count3': 11,
    'count4': 12,
    'count5': 13,
    'count6': 14,
    'count7': 15,
}

# Dout pins that will generate the counter signal.
counter_channels: Final[list[int]] = [24, 25, 26, 27, 28, 29, 30, 31]

# Channel edges where samples should be taken.
# Take a sample on the falling edge of the MSb of the counter to know its
# rolled over.
channels_capture_edge_both: Final[list[int]] = [
    channels['clk'],
    channels['dat'],
    channels['dst'],
    channels['lat'],
    channels['mtr1'],
    channels['mtr2'],
    channels['count7']
]


class DigilentDDiscovery(SignalAnalyser):
    _COUNT_FREQ: Final[int] = 10000

    def __init__(self) -> None:
        try:
            self._device: Final[DwfDevice] = pydwf.utilities.openDwfDevice(
                dwf,
                score_func=maximize_digital_in_buffer_size
            )
        except PyDwfError as exc:
            raise DeviceError(
                'Failed to initialise Digilent Digital ' +
                'Discovery analyser. Device not found.'
            ) from exc

        self._digin: Final[DigitalIn] = self._device.digitalIn
        self._digout: Final[DigitalOut] = self._device.digitalOut

        self._samples: list[NDArray[uint8]] = []
        self._timestamps: list[NDArray[float64]] = []

        self._global_counter: int = 0
        self._global_counter_lock: bool = False

        self.cleanup: Final[finalize] = weakref.finalize(self, self._cleanup)

    def _cleanup(self) -> None:
        try:
            self._device.close()
        except DwfLibraryError:
            pass

    def start_capture(self) -> None:
        self._start_counter(counter_channels, frequency=self._COUNT_FREQ)

        # Use sync mode (only capture edges).
        self._digin.dividerSet(-1)

        # Record samples only (no noise), with the pin states for each sample
        # packed into 16bits allong with a counter that can be used to
        # calculate a timestamp.
        self._digin.acquisitionModeSet(DwfAcquisitionMode.Record)
        self._digin.sampleModeSet(DwfDigitalInSampleMode.Simple)
        self._digin.sampleFormatSet(16)

        # Set the trigger for an edge on any pin.
        self._digin.triggerSourceSet(DwfTriggerSource.DetectorDigitalIn)
        self._digin.triggerSlopeSet(DwfTriggerSlope.Either)
        self._digin.triggerAutoTimeoutSet(10)

        rising = 0
        falling = 0
        for channel in channels_capture_edge_both:
            rising += 1 << channel
            falling += 1 << channel

        self._digin.triggerSet(
            level_high=0,
            level_low=0,
            edge_rise=rising,
            edge_fall=falling,
        )

        max_buffer_size = self._digin.bufferSizeInfo()
        self._digin.triggerPositionSet(max_buffer_size)
        self._digin.bufferSizeSet(max_buffer_size)

        # Start recording and wait until the prefill is full.
        self._digin.configure(reconfigure=True, start=True)
        while self._digin.status(read_data_flag=False) == DwfState.Prefill:
            pass

    def stop_capture(self) -> None:
        status = self._digin.status(read_data_flag=False)
        if status != DwfState.Ready or status != DwfState.Done:
            self._device.reset()

    def process_capture(self, timeout: timedelta = timedelta(seconds=10)) -> None:
        start_time = datetime.now()

        while self._digin.status(read_data_flag=False) == DwfState.Prefill:
            if datetime.now() >= start_time + timeout:
                raise CaptureTimeout

        # Wait for the trigger.
        while self._digin.status(read_data_flag=True) == DwfState.Armed:
            if datetime.now() >= start_time + timeout:
                raise CaptureTimeout

        # The samples in the prefill buffer when the trigger occurs make up the
        # first set of data.
        data = self._get_samples()
        if data:
            samples, timestamps = data
            self._samples.append(samples)
            self._timestamps.append(timestamps)

        while self._digin.status(read_data_flag=True) == DwfState.Triggered:
            if datetime.now() >= start_time + timeout:
                self._digout.reset()
                self._digin.reset()
                raise CaptureTimeout

            data = self._get_samples()

            if data:
                self._samples.append(data[0])
                self._timestamps.append(data[1])
            else:
                # End the capture if nothing happens for more than 1 second.
                last_timestamp: float = 0.0
                if len(self._timestamps) > 0:
                    last_timestamp = self._timestamps[-1][-1]

                current_time = self._global_counter * (1 / self._COUNT_FREQ)
                idle_time = current_time - last_timestamp
                if idle_time >= 1.0:
                    self._digout.reset()
                    self._digin.reset()
                    return

    def get_data(self) -> NDArray[np.record]:
        samples: NDArray[uint8] = np.concatenate(self._samples)
        timestamps: NDArray[float64] = np.concatenate(self._timestamps)

        samples = np.expand_dims(samples, axis=0)
        samples = np.unpackbits(samples, axis=0, count=6, bitorder='little')

        return nprec.fromarrays([
            timestamps,
            samples[0],
            samples[1],
            samples[2],
            samples[3],
            samples[4],
            samples[5]
        ],
            dtype=SampleRecord
        )

    def export_data(self, filepath: Path) -> None:
        file = open(filepath, 'w', newline='\n')
        writer = csv.writer(file, delimiter=',')
        writer.writerow([
            'Timestamp',
            'Clock',
            'Data',
            'DST',
            'Latch',
            'Motor1',
            'Motor2'
        ])

        records = self.get_data()
        for record in records:
            writer.writerow([
                record['timestamp'],
                record['clock'],
                record['data'],
                record['dst'],
                record['latch'],
                record['motor1'],
                record['motor2']
            ])

    def clear_data(self) -> None:
        self._samples.clear()
        self._timestamps.clear()
        self._global_counter = 0
        self._global_counter_lock = False

    def _get_samples(self) -> Optional[Tuple[NDArray[uint8], NDArray[float64]]]:
        '''
        Get a set of samples and their respective timestamps. If there are no
        new samples that represent a change in state of the mech, return None.

        '''
        sample_count = self._digin.statusSamplesValid()
        if sample_count == 0:
            return None

        data: NDArray[uint8] = self._digin.statusData(sample_count)

        # Split the data into the counter signal and actual data.
        samples: NDArray[uint8] = data[0::2]
        counter: NDArray[uint32] = data[1::2].astype(uint32)

        # Convert the repeating 8 bit counter to global time index.
        for i in range(0, len(counter)):
            if counter[i] >= 128 and self._global_counter_lock:
                self._global_counter_lock = False

            elif counter[i] < 128 and not self._global_counter_lock:
                self._global_counter += np.iinfo(uint8).max
                self._global_counter_lock = True

            counter[i] += self._global_counter

        # Convert the time indicies into timestamps.
        timestamps: NDArray[float64] = counter * (1 / self._COUNT_FREQ)

        # Return None if this set doesn't include any new samples that
        # represent a change in state.
        last_sample = self._samples[-1][-1] if len(self._samples) > 0 else None
        non_repeated = samples != np.r_[samples[1:], None]
        if (not np.any(non_repeated[:-1])) and samples[0] == last_sample:
            return None

        return (samples, timestamps)

    def _start_counter(self, channels: list[int], frequency: int) -> None:
        '''
        Setup a counter which will be fed into the digitalin channels to
        provide a time index for each sample.

        '''
        divider = int(self._digout.internalClockInfo() / frequency)

        for channel in channels:
            channel -= 24
            self._digout.enableSet(channel, True)

            self._digout.counterSet(channel, 1, 1)
            self._digout.typeSet(channel, DwfDigitalOutType.Pulse)
            self._digout.idleSet(channel, DwfDigitalOutIdle.Low)

            self._digout.dividerInitSet(channel, divider)
            self._digout.dividerSet(channel, divider)
            divider *= 2

        self._digout.repeatSet(0)
        self._digout.configure(start=True)

        while self._digout.status() != DwfState.Running:
            pass
