from tkinter import Tk, Canvas, PhotoImage, Frame, Scrollbar, Event
from typing import Final, Optional

import numpy as np

from .ltpd245 import LTPD245Analyser
from .signal_analyser import DigilentDDiscovery
from .printout import Printout


class Application:
    _REFRESH_RATE: Final[int] = 100

    def __init__(self) -> None:
        self._analyser: LTPD245Analyser = LTPD245Analyser(DigilentDDiscovery())

        self._root: Final[Tk] = Tk()
        self._root.title('Virtual Print Mech')

        self._root.grid_rowconfigure(0, weight=1)
        self._root.grid_columnconfigure(0, weight=1)

        self._printout_display = PrintoutDisplay(self._root, background="bisque")# , width=540, height=720)
        self._printout_display.grid(row=0, column=0, sticky='nsew', rowspan=2)

        self.update_printout()

        self._analyser.start_capture()

    def run_main_loop(self) -> None:
        self._root.mainloop()

    def update_printout(self) -> None:
        self._root.after(self._REFRESH_RATE, self.update_printout)

        self._analyser.process_available_data()
        printout = self._analyser.get_printout()
        if not printout:
            return

        self._printout_display.update_printout(printout)


class PrintoutDisplay(Frame):
    def __init__(self, master=None, printout: Optional[Printout] = None, **kw):
        super(PrintoutDisplay, self).__init__(master=master, **kw)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas: Canvas = Canvas(self, highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky='nsew')

        self.v_scroll = Scrollbar(self, orient='vertical', width=10)
        self.v_scroll.grid(row=0, column=1, sticky='ns')

        self._canvas.config(yscrollcommand=self.v_scroll.set)
        self._canvas.config(scrollregion=self._canvas.bbox('all'))
        self._canvas.bind_class(str(self._canvas), "<MouseWheel>", self.mouse_scroll)

        self.v_scroll.config(command=self._canvas.yview)

        self._image: Optional[PhotoImage] = None
        self.printout_container = self._canvas.create_image(0, 0, anchor='nw', image=None)
        self.update_printout(printout) if printout else ...

    def update_printout(self, printout: Printout) -> None:
        new_image = np.array(printout)

        height, width = new_image.shape
        data = f'P5 {width} {height} 255 '.encode() + new_image.tobytes()
        self._image = PhotoImage(width=width, height=height, data=data, format='PPM')
        self._canvas.itemconfig(self.printout_container, image=self._image)
        self._canvas.config(scrollregion=self._canvas.bbox('all'))

    def mouse_scroll(self, event: Event):
        self._canvas.yview_scroll(int(-1*(event.delta / 120)), 'units')  # For windows


if __name__ == "__main__":
    app = Application()
    app.run_main_loop()
