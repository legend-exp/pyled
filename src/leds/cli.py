from __future__ import annotations

import sys

from PyQt5 import QtWidgets

from leds.core import MainWindow


def leds_cli() -> None:
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec_()
