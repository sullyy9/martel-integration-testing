import argparse

from .app import TestRunner, TestRunnerConfig

parser = argparse.ArgumentParser()
parser.add_argument("--primary")
parser.add_argument("--usb")
parser.add_argument("--rs232")
parser.add_argument("--infrared")
parser.add_argument("--bluetooth")

args = parser.parse_args()
config = TestRunnerConfig()

config.selectors.primary_init = args.primary
config.selectors.primary_lock = False if args.primary is None else True

config.selectors.usb_init = args.usb
config.selectors.rs232_init = args.rs232
config.selectors.infrared_init = args.infrared
config.selectors.bluetooth_init = args.bluetooth

config.selectors.usb_lock = False if args.usb is None else True
config.selectors.rs232_lock = False if args.rs232 is None else True
config.selectors.infrared_lock = False if args.infrared is None else True
config.selectors.bluetooth_lock = False if args.bluetooth is None else True

app = TestRunner(config=config)
app.run()
