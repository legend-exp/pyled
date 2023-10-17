from __future__ import annotations

import sys

from core import MainWindow
from PyQt5 import QtWidgets


def leds_cli() -> None:
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec_()
