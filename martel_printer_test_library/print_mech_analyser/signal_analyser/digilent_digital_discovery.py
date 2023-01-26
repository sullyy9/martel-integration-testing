import csv
import time
import weakref
from datetime import timedelta, datetime
from pathlib import Path
from weakref import finalize
from typing import Final, Optional, Tuple

import numpy as np
from numpy import float32, int32, uint8
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
    '''
    Signal analyser implemnetation using the Digilent Digital DIscovery.
    Uses 'Sync' acquisition mode to only capture samples on signal edges.
    Additionally a counter is generated on the digital IO pins which is used to
    calculate a rough timestamp for each sample. The counter signal is fed back
    into the digital input pins so only 16 bits per sample is required.

    '''
    _COUNT_FREQ: Final[int] = 10000  # Generated counter frequency.

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
        self._timestamps: list[NDArray[float32]] = []

        # The counter embedded into the samples is only 8bits so a global
        # counter is required to track the global count.
        self._global_counter: int = 0
        self._last_count: int = 0

        self.cleanup: Final[finalize] = weakref.finalize(self, self._cleanup)

    def _cleanup(self) -> None:
        try:
            self._digout.reset()
            self._digin.reset()
            self._device.close()
        except DwfLibraryError:
            pass

    def start_capture(self) -> None:
        self._start_counter(counter_channels, frequency=self._COUNT_FREQ)

        # Use sync mode only sample on edges.
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

        # Start recording.
        self._digin.configure(reconfigure=True, start=True)

        # Slight delay required. Sample timing is inaccurate otherwise.
        # TODO Investigate.
        # Waiting for the device to enter the triggered state doesn't solve it.
        time.sleep(0.5)

    def stop_capture(self) -> None:
        status = self._digin.status(read_data_flag=False)
        if status != DwfState.Ready or status != DwfState.Done:
            self._digout.reset()
            self._digin.reset()

    def process_capture(self, timeout: timedelta = timedelta(seconds=10)) -> None:
        timeout_point = datetime.now() + timeout
        last_samples_timestamp: Optional[float] = None

        while datetime.now() < timeout_point:
            status = self._digin.status(read_data_flag=True)

            if status != DwfState.Triggered:
                continue

            data = self._get_samples()
            if data is not None:
                samples, timestamps = data
                self._samples.append(samples)
                self._timestamps.append(timestamps)
                last_samples_timestamp = self._timestamps[-1][-1]

            # If there's no new data but there's been at least 1 valid sample,
            # calculate how long the signals been idle. If more than 1 second,
            # timeout.
            elif last_samples_timestamp is not None:
                current_time = self._global_counter * (1 / self._COUNT_FREQ)
                if current_time - last_samples_timestamp >= 1.0:
                    self._digout.reset()
                    self._digin.reset()
                    return

        # Timed out
        self._digout.reset()
        self._digin.reset()
        raise CaptureTimeout

    def data_available_at_runtime(self) -> bool:
        return True

    def take_avalable_data(self) -> Optional[NDArray[np.record]]:
        status = self._digin.status(read_data_flag=True)
        if status == DwfState.Prefill:
            return None

        if status == DwfState.Armed:
            return None

        if status == DwfState.Triggered:
            data = self._get_samples()
            if data is None:
                return None

            samples, timestamps = data
            samples = np.expand_dims(samples, axis=0)
            samples = np.unpackbits(
                samples, axis=0, count=6, bitorder='little')

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

    def get_data(self) -> NDArray[np.record]:
        samples: NDArray[uint8] = np.concatenate(self._samples)
        timestamps: NDArray[float32] = np.concatenate(self._timestamps)

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

    def _get_samples(self) -> Optional[Tuple[NDArray[uint8], NDArray[float32]]]:
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
        counter: NDArray[int32] = data[1::2].astype(int32)

        # Convert the repeating 8 bit counter to global time index.
        # Check if the counter has rolled over from the last data set.
        if counter[0] < self._last_count:
            self._global_counter += (np.iinfo(uint8).max + 1)
        self._last_count = counter[-1]

        # Split the counter where it has rolled over.
        count_cycles = np.split(
            counter, np.flatnonzero(np.diff(counter) < 0) + 1)

        # For each counter run, convert it into the global counter domain.
        for i in range(0, len(count_cycles)):
            count_cycles[i] += self._global_counter

            # Dont increment global counter on the last cycle as there may not
            # be a rollover.
            if i < (len(count_cycles) - 1):
                self._global_counter += (np.iinfo(uint8).max + 1)

        # Convert the global counter into timestamps.
        timestamps: NDArray[float32] = counter * (1 / self._COUNT_FREQ)

        # Return None if this set doesn't include any new samples that
        # represent a change in state.
        last_sample = self._samples[-1][-1] if len(self._samples) > 0 else None
        non_repeated = samples[:-1] != samples[1:]
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
