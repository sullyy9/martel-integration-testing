import serial
import serial.tools.list_ports
from typing import Final, Optional, cast
from serial import Serial

from robot.api import FatalError, Failure
from robot.api.deco import keyword, library
from robot.libraries import Dialogs

from .environment import TestEnvironment

from martel_tcu import TCU, RelayChannel, MeasureChannel


def string_to_volts(string: str) -> float:
    if string.endswith("mV"):
        string = string.removesuffix("mV")
        return float(string) / 1000
    elif string.endswith("V"):
        string = string.removesuffix("V")
        return float(string)
    else:
        raise ValueError(f"{string} not recognised as a voltage")


def volts_to_str(volts: float) -> str:
    if volts > 1:
        return f"{volts:.2f}V"
    if volts * 1000 > 1:
        return f"{volts * 1000:.2f}mV"
    else:
        return f"{volts * 1_000_000:.2f}uV"


def string_to_amps(string: str) -> float:
    if string.endswith("uA"):
        string = string.removesuffix("uA")
        return float(string) / 1_000_000
    if string.endswith("mA"):
        string = string.removesuffix("mA")
        return float(string) / 1000
    elif string.endswith("A"):
        string = string.removesuffix("A")
        return float(string)
    else:
        raise ValueError(f"{string} not recognised as current")


def amps_to_str(amps: float) -> str:
    if amps > 1:
        return f"{amps:.2f}A"
    if amps * 1000 > 1:
        return f"{amps * 1000:.2f}mA"
    else:
        return f"{amps * 1_000_000:.2f}uA"


@library(scope="GLOBAL")
class TCUTestLibrary:
    def __init__(self, env: TestEnvironment = TestEnvironment()) -> None:
        self._tcu: Optional[TCU] = None

        if type(env.tcu_port) == Serial:
            self._tcu = TCU(env.tcu_port)

    @keyword("Setup TCU Test Library")
    def setup(self) -> None:
        if self._tcu is not None:
            return

        ports: Final = serial.tools.list_ports.comports()
        selected_port = Dialogs.get_selection_from_user("Select the TCU port", *ports)

        port_name: Final = next(p.name for p in ports if str(p) == selected_port)
        self._tcu = TCU(serial.Serial(port_name))

        # Disable battery and charger power by default.
        self._tcu.open_relay(RelayChannel.BATTERY_ENABLE)
        self._tcu.open_relay(RelayChannel.CHARGER_ENABLE)

    ##################################################

    @keyword("Open Power Relays")
    def open_power_relays(self) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        self._tcu.open_relay(RelayChannel.BATTERY_CONNECT)

    @keyword("Close Power Relays")
    def close_power_relays(self) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        self._tcu.close_relay(RelayChannel.CHARGER_CONNECT)

    ##################################################

    @keyword("Enable Battery Power")
    def enable_battery_power(self) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        self._tcu.close_relay(RelayChannel.BATTERY_ENABLE)

    @keyword("Disable Battery Power")
    def disable_battery_power(self) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        self._tcu.open_relay(RelayChannel.BATTERY_ENABLE)

    @keyword("Enable Charger Power")
    def enable_charger_power(self) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        self._tcu.close_relay(RelayChannel.CHARGER_ENABLE)

    @keyword("Disable Charger Power")
    def disable_charger_power(self) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        self._tcu.open_relay(RelayChannel.CHARGER_ENABLE)

    ##################################################

    @keyword("Set Battery Voltage")
    def set_battery_voltage(self, voltage: float | str) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        if type(voltage) == str:
            voltage = string_to_volts(voltage)

        millivolts: Final[int] = int(voltage * 1000)
        self._tcu.set_channel(RelayChannel.BATTERY_VOLTAGE_SET, millivolts)

    @keyword("Set Charger Voltage")
    def set_charger_voltage(self, voltage: float | str) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        if type(voltage) == str:
            voltage = string_to_volts(voltage)

        millivolts: Final[int] = int(voltage * 1000)
        self._tcu.set_channel(RelayChannel.CHARGER_VOLTAGE_SET, millivolts)

    ##################################################

    @keyword("Battery Current Should Be Between")
    def battery_current_should_be_between(
        self, min: float | str, max: float | str
    ) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        min = string_to_amps(min) if type(min) is str else cast(float, min)
        max = string_to_amps(max) if type(max) is str else cast(float, max)

        measured: Final = self._tcu.measure_channel(MeasureChannel.BATTERY_CURRENT)
        measured_amps: Final = float(measured) / 1000

        if measured_amps < min or measured_amps > max:
            raise Failure(
                "Measured battery current out of bounds\n"
                f"Measured {amps_to_str(measured_amps)}\n"
                f"Expected {amps_to_str(min)} - {amps_to_str(max)}"
            )

    @keyword("Charger Current Should Be Between")
    def charger_current_should_be_between(
        self, min: float | str, max: float | str
    ) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        min = string_to_amps(min) if type(min) is str else cast(float, min)
        max = string_to_amps(max) if type(max) is str else cast(float, max)

        measured: Final = self._tcu.measure_channel(MeasureChannel.CHARGER_CURRENT)
        measured_amps: Final = float(measured) / 1000

        if measured_amps < min or measured_amps > max:
            raise Failure(
                "Measured charger current out of bounds\n"
                f"Measured {amps_to_str(measured_amps)}\n"
                f"Expected {amps_to_str(min)} - {amps_to_str(max)}"
            )

    ##################################################

    @keyword("Battery Voltage Drop 5s Should Be Less Than")
    def battery_voltage_drop_5s_less_than(self, limit: float | str) -> None:
        if self._tcu is None:
            raise FatalError("TCU has not been setup.")

        limit = string_to_volts(limit) if type(limit) is str else cast(float, limit)

        measured: Final = self._tcu.measure_channel(
            MeasureChannel.BATTERY_VOLTAGE_DROP_5S
        )

        measured_volts: Final = float(measured) / 1000
        if measured_volts > limit:
            raise Failure(
                "Measured battery voltage drop out of bounds\n"
                f"Measured {volts_to_str(measured_volts)}\n"
                f"Expected maximum of {volts_to_str(limit)}"
            )
