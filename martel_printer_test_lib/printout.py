from pathlib import Path
import os

from PIL import Image, ImageChops, ImageDraw, ImageFont, UnidentifiedImageError

from robot.api.deco import keyword, library
from robot.api import Failure

# Exceptions


class InvalidFormat(Exception):
    pass


class SampleNotSet(Exception):
    pass


class CannotLoadSample(Exception):
    pass


@library(scope='SUITE')
class PrintoutComparison:
    def __init__(self):
        self.sample = None

        self.compare_out_dir = Path(os.getcwd(), 'output', 'compare')
        self.sample_dir = Path(os.getcwd(), 'samples')
        os.makedirs(self.compare_out_dir, exist_ok=True)

    @keyword('Load Sample ${filename}')
    def load_sample(self, filename: str):
        sample_path = Path(self.sample_dir, filename)
        try:
            sample = Image.open(sample_path)
            if sample.mode != 'L':
                raise CannotLoadSample(
                    sample_path) from InvalidFormat(sample.mode)

            self.sample = convert_to_bilevel(sample)

        except (FileNotFoundError, UnidentifiedImageError, ValueError, TypeError) as exc:
            raise CannotLoadSample(sample_path) from exc

    @keyword('Clear Sample')
    def clear_sample(self):
        self.sample = None

    @keyword('Get Sample')
    def get_sample(self) -> Image.Image | None:
        if self.sample is None:
            raise SampleNotSet
        return self.sample

    @keyword('Sample Should Match ${printout}')
    def matches(self, printout: Image.Image):
        if self.sample is None:
            raise SampleNotSet(
                'No sample has been set to compare a printout against')
        if self.sample is not None:
            diff = ImageChops.difference(
                convert_to_bilevel(printout), self.sample)
            if diff.getbbox() is None:
                return
            else:
                raise Failure('Printout does not match sample')

    @keyword(name='Save Comparison')
    def create_comparison_and_save(self, printout: Image.Image, filename: str):
        if self.sample is not None:
            diff = ImageChops.difference(
                printout.point(greyscale_to_bw), self.sample)

            # Create a comparison image. 3 printouts side by side in the order:
            # printout, sample, diff
            diff_image = create_diff_image(
                self.sample, convert_to_bilevel(printout))
            width = printout.width + self.sample.width + diff_image.width
            height = max(printout.height, self.sample.height)

            comparison = Image.new('RGB', (width, height), (255, 255, 255))
            comparison.paste(self.sample, (0, 0))
            comparison.paste(printout, (printout.width, 0))
            comparison.paste(
                diff_image, (printout.width + self.sample.width, 0))

            # Label the images
            diff_box = diff.getbbox()
            if diff_box is not None:
                draw = ImageDraw.Draw(comparison)
                fnt = ImageFont.load_default()
                draw.text((0, 0), "Sample", font=fnt, fill=(0, 0, 0))
                draw.text((printout.size[0], 0),
                          "Printout", font=fnt, fill=(0, 0, 0))

                # draw.rectangle(diff_box, outline='red')

            comparison.save(Path(self.compare_out_dir, filename))
        else:
            raise Exception('No Sample Set')

    @keyword('Save Printout')
    def save_printout(self, printout: Image.Image, filename: str):
        printout.save(Path(self.compare_out_dir, filename))


def create_diff_image(img1: Image.Image, img2: Image.Image) -> Image.Image:
    if img1.mode != '1':
        raise InvalidFormat('Image 1 has format:', img1.mode,
                            'Image must be in 1 bit per pixel (1) format')

    if img2.mode != '1':
        raise InvalidFormat('Image 2 has format:', img2.mode,
                            'Image must be in 1 bit per pixel (1) format')

    if img1.width != img2.width:
        raise InvalidFormat('Printouts must be the same width')

    black = 0
    white = 1

    # Make both images have the same height.
    # Add whitespace if nescessary.
    if img1.height < img2.height:
        tmp = Image.new('1', (img1.width, img2.height), white)
        tmp.paste(img1, (0, 0))
        img1 = tmp
    elif img2.height < img1.height:
        tmp = Image.new('1', (img2.width, img1.height), white)
        tmp.paste(img2, (0, 0))
        img2 = tmp

    diff = Image.new('RGB', (img1.width, img1.height), (255, 255, 255))

    for x in range(0, diff.width-1):
        for y in range(0, diff.height-1):
            if img1.getpixel((x, y)) == white and img2.getpixel((x, y)) == black:
                diff.putpixel((x, y), (0, 255, 0))
            elif img1.getpixel((x, y)) == black and img2.getpixel((x, y)) == white:
                diff.putpixel((x, y), (255, 0, 0))
            elif img1.getpixel((x, y)) == black and img2.getpixel((x, y)) == black:
                diff.putpixel((x, y), (0, 0, 0))
            else:
                diff.putpixel((x, y), (255, 255, 255))

    diff.show()
    return diff


def greyscale_to_bw(pixel):
    return 0 if pixel <= 254 else 255


def convert_to_bilevel(printout: Image.Image) -> Image.Image:
    if printout.mode != 'L':
        raise InvalidFormat('Image must be in greyscale mode')
    return printout.point(map_pixel_to_bw, mode='1')


def map_pixel_to_bw(pixel):
    return 0 if pixel <= 254 else 1
