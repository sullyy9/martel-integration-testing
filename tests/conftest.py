import os

from PIL import Image

from martel_printer_test.saleae_analyzer import Analyzer
from martel_printer_test.printer import Printer

import pytest

out_dir = os.path.join(os.getcwd(), 'output')
capture_dir = os.path.join(out_dir, 'captures')
printout_dir = os.path.join(out_dir, 'printout')
compare_dir = os.path.join(out_dir, 'compare')

@pytest.fixture(scope='module', autouse=True)
def create_output_directories():
    os.makedirs(capture_dir, exist_ok=True)
    os.makedirs(printout_dir, exist_ok=True)
    os.makedirs(compare_dir, exist_ok=True)


@pytest.fixture(scope='session')
def analyzer():
    analyzer_handle = Analyzer()
    yield analyzer_handle
    analyzer_handle.close()


@pytest.fixture
def printer():
    printer_handle = Printer()
    printer_handle.enable_debug()
    yield printer_handle
    printer_handle.close()

@pytest.fixture
def example_text():
    return b'Martel Instruments is a leading manufacturer and global supplier of bespoke and innovative commercial printing solutions.\n'

@pytest.fixture
def arial16_sample():
    return Image.open('./samples/arial16.png')

@pytest.fixture
def arial12_sample():
    return Image.open('./samples/arial12.png')

@pytest.fixture
def arial9_sample():
    return Image.open('./samples/arial9.png')