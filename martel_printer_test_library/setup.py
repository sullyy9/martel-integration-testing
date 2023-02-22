from enum import Enum, auto, unique
from typing import Final, Optional

import serial.tools.list_ports

from robot.libraries import Dialogs

from martel_printer.comms import SerialCommsInterface
from martel_printer import USBAutoDetect, USBPort, RS232Adapter, IrDAAdapter

from martel_print_mech_analyser import PrintMechAnalyser
from martel_print_mech_analyser import LTPD245Analyser
from martel_print_mech_analyser.signal_analyser import DigilentDDiscovery

from .tcu import RS232TCUComms, IrDATCUComms


@unique
class CommsProtocol(Enum):
    USB = auto()
    RS232 = auto()
    IrDA = auto()
    Bluetooth = auto()


PROTOCOL_INTERFACES: Final[dict[CommsProtocol, list[type[SerialCommsInterface]]]] = {
    CommsProtocol.USB: [USBAutoDetect, USBPort],
    CommsProtocol.RS232: [RS232Adapter, RS232TCUComms],
    CommsProtocol.IrDA: [IrDAAdapter, IrDATCUComms],
    CommsProtocol.Bluetooth: [],
}

PRINT_MECH_ANALYSERS: Final[list[type[PrintMechAnalyser]]] = [LTPD245Analyser]


def from_user_get_comms_interface(
    protocol: CommsProtocol,
    allow_skip: bool = True
) -> Optional[SerialCommsInterface]:

    skip_string: str = 'Skip tests requiring this protocol'
    interfaces = PROTOCOL_INTERFACES[protocol]
    if allow_skip:
        try:
            selected_interface: str = Dialogs.get_selection_from_user(
                f'Select a {protocol.name} interface:',
                *[i.__name__ for i in interfaces],
                skip_string
            )
        except RuntimeError:
            selected_interface = skip_string

    else:
        selected_interface: str = Dialogs.get_selection_from_user(
            f'Select a {protocol.name} interface:',
            *[i.__name__ for i in interfaces]
        )
    if selected_interface == skip_string:
        return None

    interface = next(i for i in interfaces if i.__name__ == selected_interface)

    if interface == type[USBAutoDetect]:
        return interface()

    ports = serial.tools.list_ports.comports()
    selected_port = Dialogs.get_selection_from_user(
        'Select a serial port for the interface',
        *ports
    )
    interface_port = next(p.name for p in ports if str(p) == selected_port)

    if interface == USBPort:
        return USBPort(interface_port)

    elif interface == RS232Adapter:
        return RS232Adapter(interface_port)
    elif interface == RS232TCUComms:
        return RS232TCUComms(interface_port)

    elif interface == IrDAAdapter:
        return IrDAAdapter(interface_port)
    elif interface == IrDATCUComms:
        return IrDATCUComms(interface_port)

    else:
        raise NotImplementedError


def from_user_get_mech_analyser(allow_skip: bool = True) -> Optional[PrintMechAnalyser]:
    skip_string: str = 'Skip tests requiring print analysis'

    if allow_skip:
        try:
            selection: str = Dialogs.get_selection_from_user(
                f'Select a print mech analyser:',
                *[i.__name__ for i in PRINT_MECH_ANALYSERS],
                skip_string
            )
        except RuntimeError:
            selection = skip_string
    else:
        selection: str = Dialogs.get_selection_from_user(
            f'Select a print mech analyser:',
            *[i.__name__ for i in PRINT_MECH_ANALYSERS],
        )

    if selection == skip_string:
        return None

    analyser = next(i for i in PRINT_MECH_ANALYSERS if i.__name__ == selection)
    if analyser == LTPD245Analyser:
        return LTPD245Analyser(DigilentDDiscovery())
    else:
        raise NotImplementedError
