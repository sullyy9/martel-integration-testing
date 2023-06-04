import argparse

from .app import TestRunner
from .selectors.types import Interface

parser = argparse.ArgumentParser()
parser.add_argument("--primary_interface")
parser.add_argument("--usb_interface")
parser.add_argument("--rs232_interface")
parser.add_argument("--infrared_interface")
parser.add_argument("--bluetooth_interface")

args = parser.parse_args()
app = TestRunner(
    primary_interface=args.primary_interface,
    usb_interface=args.usb_interface,
    rs232_interface=args.rs232_interface,
    infrared_interface=args.infrared_interface,
    bluetooth_interface=args.bluetooth_interface,
)

if args.primary_interface is not None:
    app.selectors.primary_selector.lock()

if args.usb_interface is not None:
    app.selectors.interface_selector[Interface.USB].lock()

if args.rs232_interface is not None:
    app.selectors.interface_selector[Interface.RS232].lock()

if args.infrared_interface is not None:
    app.selectors.interface_selector[Interface.INFRARED].lock()

if args.bluetooth_interface is not None:
    app.selectors.interface_selector[Interface.BLUETOOTH].lock()

app.run()
