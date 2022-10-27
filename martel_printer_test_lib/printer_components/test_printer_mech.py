import unittest
import itertools

from print_mechanism import PaperBuffer


class TestPaperBuffer(unittest.TestCase):
    def setUp(self):
        self.paper_buffer = PaperBuffer()

    def test_new_line(self):
        self.paper_buffer.new_line()
        self.assertEqual(len(self.paper_buffer.buffer), 3,
                         'Incorrect paper buffer length')

        for _ in itertools.repeat(None, 5):
            self.paper_buffer.new_line()
        self.assertEqual(len(self.paper_buffer.buffer), 8,
                         'Incorrect paper buffer length')
