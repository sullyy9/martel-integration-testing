import serial.tools.list_ports
from serial import Serial
from enum import Enum, auto, unique
from typing import Final, Optional


from robot.libraries import Dialogs

from martel_printer.comms import CommsInterface

from martel_print_mech_analyser import PrintMechAnalyser
from martel_print_mech_analyser import LTPD245Analyser
from martel_print_mech_analyser.signal_analyser import DigilentDDiscovery

from martel_tcu import TCU, RS232ThroughTCU, IrDAThroughTCU, BluetoothThroughTCU


@unique
class CommsProtocol(Enum):
    USB = auto()
    RS232 = auto()
    IrDA = auto()
    Bluetooth = auto()


INTERFACES: Final = {
    CommsProtocol.USB: [Serial],
    CommsProtocol.RS232: [Serial, RS232ThroughTCU],
    CommsProtocol.IrDA: [Serial, IrDAThroughTCU],
    CommsProtocol.Bluetooth: [BluetoothThroughTCU],
}

PRINT_MECH_ANALYSERS: Final = [LTPD245Analyser]


def from_user_get_comms_interface(
    protocol: CommsProtocol, allow_skip: bool = True
) -> Optional[CommsInterface]:
    skip_string: str = "Skip tests requiring this protocol"

    options: list[str] = [i.__name__ for i in INTERFACES[protocol]]

    # Replace the serial option with COM ports.
    com_ports = serial.tools.list_ports.comports()
    if Serial.__name__ in options:
        options.remove(Serial.__name__)
        for port in com_ports:
            options.append(str(port))

    if allow_skip:
        options.append(skip_string)

    try:
        selected_interface: str = Dialogs.get_selection_from_user(
            f"Select a {protocol.name} interface:", *options
        )
    except RuntimeError:
        return None
    
    if selected_interface == skip_string:
        return None

    # If a COM port was selected.
    try:
        port = next(p.name for p in com_ports if str(p) == selected_interface)
        return Serial(port)
    except StopIteration:
        pass

    interface = next(
        i for i in INTERFACES[protocol] if i.__name__ == selected_interface
    )

    # Get the com port for the interface
    selected_port = Dialogs.get_selection_from_user(
        "Select a serial port for the interface", *com_ports
    )
    interface_port = next(p.name for p in com_ports if str(p) == selected_port)

    serial_port = Serial(interface_port)

    if interface == RS232ThroughTCU:
        return RS232ThroughTCU(TCU(serial_port))

    elif interface == IrDAThroughTCU:
        return IrDAThroughTCU(TCU(serial_port))

    elif interface == BluetoothThroughTCU:
        return BluetoothThroughTCU(TCU(serial_port))

    else:
        raise NotImplementedError


def from_user_get_mech_analyser(allow_skip: bool = True) -> Optional[PrintMechAnalyser]:
    skip_string: str = "Skip tests requiring print analysis"

    if allow_skip:
        try:
            selection: str = Dialogs.get_selection_from_user(
                f"Select a print mech analyser:",
                *[i.__name__ for i in PRINT_MECH_ANALYSERS],
                skip_string,
            )
        except RuntimeError:
            selection = skip_string
    else:
        selection: str = Dialogs.get_selection_from_user(
            f"Select a print mech analyser:",
            *[i.__name__ for i in PRINT_MECH_ANALYSERS],
        )

    if selection == skip_string:
        return None

    analyser = next(i for i in PRINT_MECH_ANALYSERS if i.__name__ == selection)
    if analyser == LTPD245Analyser:
        return LTPD245Analyser(DigilentDDiscovery())
    else:
        raise NotImplementedError
