import os
import weakref
import threading
from pathlib import Path
from typing import Final, Optional, Self
from datetime import timedelta
from weakref import finalize
from enum import Enum

from saleae import automation
from saleae.automation import Capture, Manager, DeviceDesc
from saleae.automation.errors import Logic2AlreadyRunningError


class PinConfig(int, Enum):
    SPICL = 0
    SPIDAT = 1
    LATCH = 2
    DST = 3
    MOTORA_L = 4
    MOTORB_L = 5
    STEPPER_EN = 6


TRIGGER_CAPTURE_CONFIG = automation.CaptureConfiguration(
    capture_mode=automation.DigitalTriggerCaptureMode(
        automation.DigitalTriggerType.PULSE_HIGH,
        PinConfig.STEPPER_EN,
        min_pulse_width_seconds=0.1,
        max_pulse_width_seconds=30,
        after_trigger_seconds=0.1
    )
)

DEVICE_CONFIG = automation.LogicDeviceConfiguration(
    enabled_digital_channels=list(PinConfig),
    digital_sample_rate=40_000_000,
)


class AnlayserInitError(Exception):
    pass


class AnalyserExportError(Exception):
    pass

# TODO Should implement the SignalAnalyser protocol. 
class SaleaeLogic8:
    __slots__ = ('__weakref__', '_manager', '_device', '_capture',
                 '_capture_running', 'cleanup')

    def __init__(self) -> None:
        self._manager: Final[Manager]
        self._device: Final[DeviceDesc]

        self._capture: Optional[Capture] = None
        self._capture_running: bool = False

        self.cleanup: Final[finalize]

        try:
            self._manager = Manager.launch()
        except Logic2AlreadyRunningError:
            self._manager = Manager.connect()

        devices = self._manager.get_devices()
        if len(devices) < 1:
            raise AnlayserInitError('Cannot find a compatible logic analyser')
        self._device = devices.pop(0)

        self.cleanup = weakref.finalize(self, self._cleanup)

    def __enter__(self) -> Self:
        return self

    def __del__(self) -> None:
        self.cleanup()

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.cleanup()

    def _cleanup(self) -> None:
        self.clear_capture()
        self._manager.close()

    def start_timed_print_capture(
        self,
        duration: timedelta = timedelta(seconds=10)
    ) -> None:
        self.clear_capture()

        capture_configuration = automation.CaptureConfiguration(
            capture_mode=automation.TimedCaptureMode(
                duration_seconds=duration.seconds)
        )

        self._capture = self._manager.start_capture(
            device_id=self._device.device_id,
            device_configuration=DEVICE_CONFIG,
            capture_configuration=capture_configuration
        )

        self._capture_running = True

    def start_print_capture(self) -> None:
        self.clear_capture()

        self._capture = self._manager.start_capture(
            device_id=self._device.device_id,
            device_configuration=DEVICE_CONFIG,
            capture_configuration=TRIGGER_CAPTURE_CONFIG
        )

        self._capture_running = True

    def clear_capture(self) -> None:
        if self._capture:
            self._capture = self._capture.close()

    def wait_until_capture_complete(self, timeout: float) -> None:
        """
        Wait until the currently running capture is complete.

        Parameters
        ----------
            Maximum time in seconds to wait for the capture to complete.

        Raises
        ------
        TimeoutError
            If the capture fails to complete within the given timeframe.

        """
        if self._capture:
            timer = threading.Timer(timeout, self._capture.stop)
            timer.start()
            self._capture.wait()

            if timer.is_alive():
                timer.cancel()
            else:
                raise TimeoutError(
                    'Capture failed to complete within the given timeframe.'
                )

    def export_capture(self, path: Path) -> None:
        if self._capture is None:
            raise AnalyserExportError('Cannot export capture as none exists.')

        self._capture.export_raw_data_csv(
            str(path.parent),
            digital_channels=list(PinConfig)
        )

        if path.name != 'digital.csv':
            os.replace(Path(path.parent, 'digital.csv'), path)