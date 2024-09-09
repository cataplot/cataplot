"""
cataplot main entry point
"""
# from dataclasses import dataclass
import sys
import time

# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QEvent, QModelIndex, QPoint
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                               QMessageBox, QInputDialog, QMenu, QTreeView)
from PySide6.QtGui import QStandardItemModel, QStandardItem

import pyqtgraph as pg

from .pyside_ui_loader import load_ui

from .command_palette import CommandPalette

# NB: You must re-run `pyside6-rcc.exe resources.rc -o resources_rc.py` any time
# the resources change.
#
# Ignore the unused import warning, as it is necessary to load the resources by
# importing them.
from . import resources_rc  # pylint: disable=unused-import

from . import treeview

# from .providers import BaseProvider
from . import provider_manager


def dummy_command(_app, crumbs, progress_signal, delay:float=0):
    """
    Simulates a long-running command that reports progress through a signal.

    """
    print(f"dummy_command(app={_app}, {crumbs}, delay={delay})")
    if len(crumbs) == 1:
        for i in range(int(delay / 0.1)):
            time.sleep(0.1)
            progress_signal.emit(i + 1)
        return "sub-command", ["foos", "bars", "bazes"]

    if len(crumbs) == 2:
        if crumbs[1] == "foos":
            return "sub-command", ["foo1", "foo2", "foo3"]
        if crumbs[1] == "bars":
            return "sub-command", ["bar1", "bar2", "bar3"]
        if crumbs[1] == "bazes":
            return "sub-command", ["baz1", "baz2", "baz3"]

    # if len(crumbs) == 3:
    #     print(f"{'.'.join(crumbs)}()")  # e.g. "sub-command.sub-sub-command.foo1"

    return "completed", []

def cmd_add_item(app, crumbs, _progress_signal):
    """
    Adds an item to a plot
    """
    if len(crumbs) == 1:
        # First menu level: sub-menus for each provider that's available in the
        # application.
        providers = app.get_providers()
        return 'sub-command', [provider.name for provider in providers]

class PlotManager(QWidget):
    """Widget to hold multiple pyqtgraph plots and link their x-axes."""

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.plots = []
        self.first_plot = None  # Reference to the first plot for x-axis linking

    def add_plot(self, name):
        """Add a new plot to the widget and link its x-axis to the first plot."""
        plot = pg.PlotWidget(title=name)
        self.layout.addWidget(plot)
        self.plots.append(plot)

        # Link x-axis to the first plot's x-axis if it exists
        if self.first_plot is None:
            self.first_plot = plot
        else:
            plot.plotItem.setXLink(self.first_plot.plotItem)  # Link x-axis

        return plot

    def remove_plot(self, index):
        """Remove a plot by index."""
        plot = self.plots.pop(index)
        self.layout.removeWidget(plot)
        plot.deleteLater()


class TreeModel(QStandardItemModel):
    """Tree model to represent plots and curves in a tree view."""

    def __init__(self):
        super().__init__()
        self.setHorizontalHeaderLabels(['Plots and Curves'])

    def add_plot(self, name):
        """Add a new plot entry to the tree."""
        plot_item = QStandardItem(name)
        plot_item.setEditable(True)  # Allow the plot name to be edited
        self.appendRow(plot_item)
        return plot_item

    def add_curve(self, plot_item, curve_name):
        """Add a curve under the plot entry."""
        curve_item = QStandardItem(curve_name)
        curve_item.setEditable(False)  # Curves are not editable
        plot_item.appendRow(curve_item)


class MainWindow(QMainWindow):
    def __init__(self, ui_filename, parent=None):
        super().__init__(parent)
        load_ui(ui_filename, self, custom_widgets={'TreeView': treeview.TreeView})

        # Initialize the command palette
        self.command_palette = CommandPalette(self)
        self.command_palette.add_command("Slow command", dummy_command, delay=3.0)
        self.command_palette.add_command("Fast command", dummy_command, delay=0.5)
        self.command_palette.add_command("Add item", cmd_add_item)

        # Add the command palette to the main window
        self.command_palette.setVisible(False)

        # Install an event filter to detect clicks outside the command palette
        self.installEventFilter(self)

        self.providers = []

        # print('providers', BaseProvider.__subclasses__())

        self.provider_manager = provider_manager.ProviderManager(self)
        # Make provider_manager modal to prevent user interaction with other
        # windows while the manager is open.
        # self.provider_manager.setWindowModality(Qt.ApplicationModal)
        self.provider_manager.setWindowModality(Qt.WindowModal)

        self.con_mgr_action.triggered.connect(self.handle_con_mgr_action)


        self.tree_model = TreeModel()
        self.tree_view.setModel(self.tree_model)

        self.plot_manager = PlotManager()
        self.tab_widget.addTab(self.plot_manager, "Tab1")

        self.splitter.setStretchFactor(0, 1)  # Make the plot area expand more

        self.tree_model.dataChanged.connect(self.on_item_changed)

        # Set up context menu for the tree view
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.open_context_menu)

        # Connect the tree view to handle selections
        self.tree_view.selectionModel().currentChanged.connect(self.on_tree_selection_changed)

        # Enable double-click to edit the plot names in place
        self.tree_view.setEditTriggers(QTreeView.DoubleClicked | QTreeView.EditKeyPressed)

        self.tree_model.dataChanged.connect(self.on_item_changed)

        self.initialize_plots()


    def on_item_changed(self, top_left: QModelIndex, bottom_right: QModelIndex):
        """Update the pyqtgraph plot title when an item in the tree view is renamed."""
        item = self.tree_model.itemFromIndex(top_left)

        # Check if the item is a plot (parent is None)
        if item and item.parent() is None:
            plot_index = top_left.row()  # Get the index of the plot
            new_plot_name = item.text()  # Get the new plot name

            # Update the corresponding plot's title in the PlotManager
            plot_widget = self.plot_manager.plots[plot_index]
            plot_widget.setTitle(new_plot_name)

    def initialize_plots(self):
        """Create some initial plots and curves."""
        plot1_item = self.tree_model.add_plot("Plot 1")
        plot1 = self.plot_manager.add_plot("Plot 1")
        self.tree_model.add_curve(plot1_item, "Curve 1")
        plot1.plot([0, 1, 2, 3], [10, 20, 10, 30], pen='r')  # Red curve

        plot2_item = self.tree_model.add_plot("Plot 2")
        plot2 = self.plot_manager.add_plot("Plot 2")
        self.tree_model.add_curve(plot2_item, "Curve 1")
        self.tree_model.add_curve(plot2_item, "Curve 2")
        plot2.plot([0, 1, 2, 3], [30, 40, 20, 10], pen='g')  # Green curve
        plot2.plot([0, 1, 2, 3], [15, 25, 35, 5], pen='b')   # Blue curve

    def on_tree_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        """Handle tree view selection changes to highlight the selected plot/curve."""
        selected_item = self.tree_model.itemFromIndex(current)
        if selected_item:
            # Handle when a plot or curve is selected
            if selected_item.parent() is None:
                # A plot is selected
                print(f"Selected plot: {selected_item.text()}")
            else:
                # A curve under a plot is selected
                print(f"Selected curve: {selected_item.text()} (under {selected_item.parent().text()})")

    def open_context_menu(self, position: QPoint):
        """Create and open the context menu when right-clicking on the tree view."""
        indexes = self.tree_view.selectedIndexes()
        selected_item = self.tree_model.itemFromIndex(indexes[0]) if indexes else None

        # Create the context menu
        context_menu = QMenu(self)

        if not selected_item or selected_item.parent() is None:
            # If the selected item is not a curve...
            context_menu.addAction("&Add Plot", self.add_plot)

        if selected_item and selected_item.parent() is None:
            # If a plot is selected...
            context_menu.addAction("&Rename Plot", lambda: self.rename_plot(selected_item))
            context_menu.addAction("&Delete Plot", lambda: self.delete_plot(selected_item))

        if selected_item and selected_item.parent() is not None:
            # If the selected item is a curve...
            context_menu.addAction("&Delete Curve")
            context_menu.addAction("P&roperties")

        # Open the context menu
        context_menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def add_plot(self):
        """Add a new plot both to the model and plot manager."""
        plot_name, ok = QInputDialog.getText(self, "Add Plot", "Enter plot name:")
        if ok and plot_name:
            # Add to tree model
            plot_item = self.tree_model.add_plot(plot_name)
            # Add to plot manager
            self.plot_manager.add_plot(plot_name)

    def rename_plot(self, plot_item):
        """Rename an existing plot by entering inline edit mode."""
        # Get the QModelIndex for the plot item
        index = self.tree_model.indexFromItem(plot_item)

        # Programmatically trigger edit mode in the QTreeView
        self.tree_view.edit(index)

    def delete_plot(self, plot_item):
        """Delete a plot from the model and the plot manager."""
        reply = QMessageBox.question(self, 'Delete Plot', f"Are you sure you want to delete '{plot_item.text()}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Find the index of the plot in the model
            index = self.tree_model.indexFromItem(plot_item).row()
            # Remove from plot manager
            self.plot_manager.remove_plot(index)
            # Remove from model
            self.tree_model.removeRow(index)

    def handle_con_mgr_action(self):
        """Shows the provider manager window when the action is triggered."""
        self.provider_manager.show()

    def add_provider(self, provider):
        """Adds a provider to the list of available data providers."""
        self.providers.append(provider)

    def get_providers(self):
        """Returns a list of available data providers."""
        return self.providers

    def eventFilter(self, obj, event):
        # If the Escape key is pressed, hide the command palette
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.command_palette.hide()
            return True
        # If ctrl+P is pressed, show the command palette
        if ((event.type() == QEvent.KeyPress) and
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
