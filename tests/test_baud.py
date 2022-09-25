import os

import pytest
from PIL import Image

from martel_printer_test.printer_mech import MechInputRecords, PrintMechState
import martel_printer_test.compare as compare
from martel_printer_test.compare import ImagesMatch

from tests.conftest import capture_dir, printout_dir, compare_dir

@pytest.fixture
def baud_sample():
    return Image.open('./samples/text.png')


def test_baud_600(analyzer, printer, example_text, baud_sample, request):

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
        comparison = compare.print_with_sample(printout, baud_sample)
        comparison.save(os.path.join(compare_dir, img_filename))
        comparison.show(title=request.node.name)


def test_baud_1200(analyzer, printer, example_text, baud_sample, request):
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
        comparison = compare.print_with_sample(printout, baud_sample)
        comparison.save(os.path.join(compare_dir, img_filename))
        comparison.show(title=request.node.name)
