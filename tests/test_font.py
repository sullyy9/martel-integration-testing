import os
import time

import pytest
from PIL import Image

from martel_printer_test.printer_mech import MechInputRecords, PrintMechState
import martel_printer_test.compare as compare
from martel_printer_test.compare import ImagesMatch

from tests.conftest import capture_dir, printout_dir, compare_dir


@pytest.fixture
def arial16_setup_teardown(printer):
    printer.set_option(5, 1)
    printer.reset()
    time.sleep(2)
    yield
    printer.set_option(5, 1)
    printer.reset()
    time.sleep(2)


@pytest.fixture
def arial12_setup_teardown(printer):
    printer.set_option(5, 2)
    printer.reset()
    time.sleep(2)
    yield
    printer.set_option(5, 1)
    printer.reset()
    time.sleep(2)


@pytest.fixture
def arial9_setup_teardown(printer):
    printer.set_option(5, 3)
    printer.reset()
    time.sleep(2)
    yield
    printer.set_option(5, 1)
    printer.reset()
    time.sleep(2)


def test_font_arial16(analyzer, printer, arial16_setup_teardown, example_text, arial16_sample, request):

    csv_filename = request.node.name + '.csv'
    img_filename = request.node.name + '.png'

    analyzer.start_print_capture(duration=5.0)
    printer.send(example_text)
    analyzer.wait_for_completion()
    analyzer.export_capture(capture_dir, filename=csv_filename)

    with MechInputRecords(os.path.join(capture_dir, csv_filename)) as mech_records:
        print_mech: PrintMechState = PrintMechState(next(mech_records))
        for record in mech_records:
            print_mech.update(record)

    printout: Image.Image = print_mech.get_paper_image()
    printout.save(os.path.join(printout_dir, img_filename))

    with pytest.raises(ImagesMatch):
        comparison = compare.print_with_sample(printout, arial16_sample)
        comparison.save(os.path.join(compare_dir, img_filename))
        comparison.show(title=request.node.name)


def test_font_arial12(analyzer, printer, arial12_setup_teardown, example_text, arial12_sample, request):

    csv_filename = request.node.name + '.csv'
    img_filename = request.node.name + '.png'

    analyzer.start_print_capture(duration=5.0)
    printer.send(example_text)
    analyzer.wait_for_completion()
    analyzer.export_capture(capture_dir, filename=csv_filename)

    with MechInputRecords(os.path.join(capture_dir, csv_filename)) as mech_records:
        print_mech = PrintMechState(next(mech_records))
        for record in mech_records:
            print_mech.update(record)

    printout = print_mech.get_paper_image()
    printout.save(os.path.join(printout_dir, img_filename))

    with pytest.raises(ImagesMatch):
        comparison = compare.print_with_sample(printout, arial12_sample)
        comparison.save(os.path.join(compare_dir, img_filename))
        comparison.show(title=request.node.name)


def test_font_arial9(analyzer, printer, arial9_setup_teardown, example_text, arial9_sample, request):

    csv_filename = request.node.name + '.csv'
    img_filename = request.node.name + '.png'

    analyzer.start_print_capture(duration=5.0)
    printer.send(example_text)
    analyzer.wait_for_completion()
    analyzer.export_capture(capture_dir, filename=csv_filename)

    with MechInputRecords(os.path.join(capture_dir, csv_filename)) as mech_records:
        print_mech = PrintMechState(next(mech_records))
        for record in mech_records:
            print_mech.update(record)

    printout = print_mech.get_paper_image()
    printout.save(os.path.join(printout_dir, img_filename))

    with pytest.raises(ImagesMatch):
        comparison = compare.print_with_sample(printout, arial9_sample)
        comparison.save(os.path.join(compare_dir, img_filename))
        comparison.show(title=request.node.name)
