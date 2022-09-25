from time import time
from pathlib import Path
import os

from PIL import Image

from printer_mech import MechInputRecords, PrintMechState
from analyser import Analyser, AnlayserNotFound
from printer import Printer, PrinterNotFound
import compare


def main():
    print()
    print("Start")
    print("--------------------")

    # Create output directories.
    out_dir = Path(os.getcwd(), 'output')
    capture_out_dir = Path(out_dir, 'captures')
    printer_out_dir = Path(out_dir, 'printout')
    compare_out_dir = Path(out_dir, 'compare')
    os.makedirs(capture_out_dir, exist_ok=True)
    os.makedirs(printer_out_dir, exist_ok=True)
    os.makedirs(compare_out_dir, exist_ok=True)

    try:
        printer = Printer()
        printer.usb.connect()
        print("Connected to printer on: ", printer.usb.get_port_name())

        # Start self-test and capture
        print('Begining self test')

        printer.enable_debug()
        printer.print_selftest()

        printer.wait_until_print_complete()

        selftest_printout = printer.get_last_printout()

        selftest_printout.save(Path(printer_out_dir, 'selftest.png'))

        comparison = compare.print_with_sample(
            selftest_printout, Image.open('./samples/selftest.png'))
        comparison.save(Path(compare_out_dir, 'selftest.png'))
        comparison.show()

        print('--------------------')
        print('Complete')
        print()

    except (AnlayserNotFound, PrinterNotFound) as exc:
        print('Error -', exc)


if __name__ == "__main__":
    main()
