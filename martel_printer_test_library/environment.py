from enum import StrEnum
import pickle
from pathlib import Path
from typing import Self
from dataclasses import dataclass
from serial import Serial

from martel_printer.comms import CommsInterface


class Skip:
    pass


class PrinterInterface(StrEnum):
    USB = "USB"
    RS232 = "RS232"
    INFRARED = "Infrered"
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


def get_variables(environment_file_path: str) -> dict:
    return {"ENVIRONMENT": TestEnvironment.load(Path(environment_file_path))}
