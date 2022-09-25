from pathlib import Path
import os

from PIL import Image, ImageChops, ImageDraw, ImageFont

from robot.api.deco import keyword, library
from robot.api import Failure


@library(scope='SUITE')
class PrintoutComparison:
    def __init__(self):
        self.sample = None

        self.compare_out_dir = Path(os.getcwd(), 'output', 'compare')
        self.sample_dir = Path(os.getcwd(), 'samples')
        os.makedirs(self.compare_out_dir, exist_ok=True)

    @keyword(name='Load Sample ${filename}')
    def load_sample(self, filename: str):
        self.sample = Image.open(
            Path(self.sample_dir, filename)).point(greyscale_to_bw)

    def clear_sample(self):
        self.sample = None

    @keyword('Get Sample')
    def get_sample(self) -> Image.Image | None:
        if self.sample is not None:
            return self.sample

    @keyword('Sample Should Match ${printout}')
    def matches(self, printout: Image.Image):
        if self.sample is not None:
            diff = ImageChops.difference(
                printout.point(greyscale_to_bw), self.sample)
            if diff.getbbox() is None:
                return
            else:
                raise Failure('Printout does not match sample')

        raise Exception('No Sample Set')

    @keyword(name='Save Comparison')
    def create_comparison_and_save(self, printout: Image.Image, filename: str):
        if self.sample is not None:
            diff = ImageChops.difference(
                printout.point(greyscale_to_bw), self.sample)

            # Create a comparison image.
            width = printout.size[0] + self.sample.size[0]
            height = max(printout.size[1], self.sample.size[1])
            comparison = Image.new('RGB', (width, height), (255, 255, 255))
            comparison.paste(printout, (0, 0))
            comparison.paste(self.sample, (printout.size[0], 0))

            # Label the images
            diff_box = diff.getbbox()
            if diff_box is not None:
                draw = ImageDraw.Draw(comparison)
                fnt = ImageFont.load_default()
                draw.text((0, 0), "Printout", font=fnt, fill=(0, 0, 0))
                draw.text((printout.size[0], 0),
                          "Sample", font=fnt, fill=(0, 0, 0))

                draw.rectangle(diff_box, outline='red')

            comparison.save(Path(self.compare_out_dir, filename))
        else:
            raise Exception('No Sample Set')


@keyword('Save Printout')
def save_printout(printout: Image.Image, filepath_str: str):
    filepath = Path(filepath_str)
    os.makedirs(filepath.parent, exist_ok=True)
    printout.save(filepath)


class ImagesMatch(Exception):
    pass


def greyscale_to_bw(pixel):
    return 0 if pixel < 254 else 255
