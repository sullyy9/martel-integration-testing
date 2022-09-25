from pathlib import Path
import os
import time

from saleae import automation

from robot.api.deco import keyword, library

SPICL = 0
SPIDAT = 1
LATCH = 2
DST = 3
MOTORA_L = 4
MOTORB_L = 5
STEPPER_EN = 6

class AnlayserNotFound(Exception):
    pass

@library(scope='GLOBAL')
class Analyser:
    def __init__(self):
        self.manager = None
        self.device = None
        self.current_capture = None
        self.captures = []

    
    def __del__(self):
        self.end()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__del__()
    
    def start(self):
        if self.manager is None:
            self.manager = automation.Manager.launch()
        devices = self.manager.get_devices()
        if len(devices) < 1:
            raise AnlayserNotFound('Cannot find the analyser')
        
        self.device = devices.pop(0)

    def end(self):
        if self.manager is not None:
            self.manager = self.manager.close()
    
    def is_running(self) -> bool:
        return False if self.manager is None else True

    def start_timed_print_capture(self, duration: float = 10.0):
        device_configuration = automation.LogicDeviceConfiguration(
            enabled_digital_channels=[0, 1, 2, 3, 4, 5],
            digital_sample_rate=25_000_000,
        )

        capture_configuration = automation.CaptureConfiguration(
            capture_mode=automation.TimedCaptureMode(duration_seconds=duration)
        )

        if self.manager is not None and self.device is not None:
            if self.current_capture is not None:
                self.captures.append(self.current_capture)

            self.current_capture = self.manager.start_capture(
                device_id=self.device.device_id,
                device_configuration=device_configuration,
                capture_configuration=capture_configuration
            )

    def start_print_capture(self):
        device_configuration = automation.LogicDeviceConfiguration(
            enabled_digital_channels=[0, 1, 2, 3, 4, 5, STEPPER_EN],
            digital_sample_rate=25_000_000,
        )

        capture_configuration = automation.CaptureConfiguration(
            capture_mode=automation.DigitalTriggerCaptureMode(
                automation.DigitalTriggerType.PULSE_HIGH,
                STEPPER_EN,
                min_pulse_width_seconds=0.1,
                max_pulse_width_seconds=30,
                after_trigger_seconds=0.1
            )
        )

        if self.manager is not None and self.device is not None:
            if self.current_capture is not None:
                self.captures.append(self.current_capture)
            self.current_capture = self.manager.start_capture(
                device_id=self.device.device_id,
                device_configuration=device_configuration,
                capture_configuration=capture_configuration
            )
        else:
            print('Capture failed to start')

    def clear_all_captures(self):
        for capture in self.captures:
            capture.close()
        if self.current_capture is not None:
            self.current_capture = self.current_capture.close()
    
    def wait_for_completion(self):
        if self.current_capture is not None:
            self.current_capture.wait()
    
    def export_capture(self, path: Path):
        if self.current_capture is not None:
            self.current_capture.export_raw_data_csv(str(path.parent), digital_channels=[0, 1, 2, 3, 4, 5])
            if path.name != 'digital.csv':
                os.replace(Path(path.parent, 'digital.csv'), path)
        

