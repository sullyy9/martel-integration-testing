from enum import StrEnum
import pickle
from pathlib import Path
from typing import Self
from dataclasses import dataclass
from serial import Serial

from martel_printer.comms import CommsInterface
from martel_tcu.tcu_comms import CommsThroughTCU

class Skip:
    pass


class PrinterInterface(StrEnum):
    USB = "USB"
    RS232 = "RS232"
    INFRARED = "Infrared"
    BLUETOOTH = "Bluetooth"


@dataclass
class TestEnvironment:
    tcu_port: Serial | Skip | None = None

    usb_interface: CommsInterface | Skip | None = None
    rs232_interface: CommsInterface | Skip | None = None
    infrared_interface: CommsInterface | Skip | None = None
    bluetooth_interface: CommsInterface | Skip | None = None

    debug_interface: CommsInterface | Skip | None = None

    def save(self, file) -> None:
        pickle.dump(self, file)

    @classmethod
    def load(cls, path: Path) -> Self:
        with open(path, mode="rb") as file:
            return pickle.load(file)

    @property
    def has_rs232_wakeup(self) -> bool:
        return not (
            self.rs232_interface is None or isinstance(self.rs232_interface, Skip)
        )

    @property
    def has_rs232_through_tcu(self) -> bool:
        return isinstance(self.rs232_interface, CommsThroughTCU)


def get_variables(environment_file_path: str | None) -> dict:
    if environment_file_path is None or len(environment_file_path) == 0:
        return {"ENVIRONMENT": TestEnvironment()}
    
    return {"ENVIRONMENT": TestEnvironment.load(Path(environment_file_path))}
