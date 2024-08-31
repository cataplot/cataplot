"""
cataplot main entry point
"""
import sys
import time

# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QEvent
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow

from .pyside_ui_loader import load_ui

from .command_palette import CommandPalette

# NB: You must re-run `pyside6-rcc.exe resources.rc -o resources_rc.py` any time
# the resources change.
#
# Ignore the unused import warning, as it is necessary to load the resources by
# importing them.
from . import resources_rc  # pylint: disable=unused-import

from . import treeview


def long_running_cmd(_args, progress_signal):
    """
    Simulates a long-running command that reports progress through a signal.
    """
    for i in range(20):
        time.sleep(0.1)
        progress_signal.emit(i + 1)
    # result_signal.emit("completed", [])
    return "sub-command", ["Result 1", "Result 2", "Result 3"]

class MainWindow(QMainWindow):
    def __init__(self, ui_filename, parent=None):
        super().__init__(parent)
        load_ui(ui_filename, self, custom_widgets={'TreeView': treeview.TreeView})

        # Initialize the command palette
        self.command_palette = CommandPalette(self)

        self.command_palette.add_command("Long-running command", long_running_cmd)

        # Add the command palette to the main window
        self.command_palette.setVisible(False)

        # Install an event filter to detect clicks outside the command palette
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        # If the Escape key is pressed, hide the command palette
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.command_palette.setVisible(False)
            return True
        # If ctrl+P is pressed, show the command palette
        elif ((event.type() == QEvent.KeyPress) and
              (event.key() == Qt.Key_P) and
              (event.modifiers() & Qt.ControlModifier)):
            self.command_palette.show()
            return True
        return super().eventFilter(obj, event)

def main():
    # NOTE: There appears to be a bug in PySide6 that requires
    # `LOADER = QUiLoader()` here (specifically, it must be defined before
    # the QApplication and MainWindow are created). If this line is
    # not present, the application will hang with no error message.
    loader = QUiLoader()  # pylint: disable=unused-variable
    app = QApplication(sys.argv)
    module_root = sys.modules[__name__].__file__
    # It is assumed that the UI file has the same name as the module
    ui_filename = module_root.replace('.py', '.ui')
    window = MainWindow(ui_filename)
    window.show()
    sys.exit(app.exec())
