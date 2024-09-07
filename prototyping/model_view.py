"""
Mock-up of a time-series plotting application using PySide6 and pyqtgraph using
a model / view architecture.
"""

import sys

# pylint: disable=no-name-in-module
from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import (QApplication, QMainWindow, QSplitter, QTreeView,
                               QVBoxLayout, QWidget)
from PySide6.QtGui import QStandardItemModel, QStandardItem
import pyqtgraph as pg

class PlotManager(QWidget):
    """Widget to hold multiple pyqtgraph plots."""

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.plots = []

    def add_plot(self, name):
        """Add a new plot to the widget."""
        plot = pg.PlotWidget(title=name)
        self.layout.addWidget(plot)
        self.plots.append(plot)
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
        self.appendRow(plot_item)
        return plot_item

    def add_curve(self, plot_item, curve_name):
        """Add a curve under the plot entry."""
        curve_item = QStandardItem(curve_name)
        plot_item.appendRow(curve_item)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main layout as a splitter to divide tree view and plot area
        splitter = QSplitter()
        self.setCentralWidget(splitter)

        # Left side: Tree view
        self.tree_view = QTreeView()
        self.model = TreeModel()
        self.tree_view.setModel(self.model)
        splitter.addWidget(self.tree_view)

        # Right side: Plot manager
        self.plot_manager = PlotManager()
        splitter.addWidget(self.plot_manager)

        splitter.setStretchFactor(1, 1)  # Make the plot area expand more

        # Initialize with some plots and curves
        self.initialize_plots()

        # Connect the tree view to handle selections
        self.tree_view.selectionModel().currentChanged.connect(self.on_tree_selection_changed)

    def initialize_plots(self):
        """Create some initial plots and curves."""
        plot1_item = self.model.add_plot("Plot 1")
        plot1 = self.plot_manager.add_plot("Plot 1")
        self.model.add_curve(plot1_item, "Curve 1")
        plot1.plot([0, 1, 2, 3], [10, 20, 10, 30], pen='r')  # Red curve

        plot2_item = self.model.add_plot("Plot 2")
        plot2 = self.plot_manager.add_plot("Plot 2")
        self.model.add_curve(plot2_item, "Curve 1")
        self.model.add_curve(plot2_item, "Curve 2")
        plot2.plot([0, 1, 2, 3], [30, 40, 20, 10], pen='g')  # Green curve
        plot2.plot([0, 1, 2, 3], [15, 25, 35, 5], pen='b')   # Blue curve

    def on_tree_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        """Handle tree view selection changes to highlight the selected plot/curve."""
        selected_item = self.model.itemFromIndex(current)
        if selected_item:
            # Handle when a plot or curve is selected
            if selected_item.parent() is None:
                # A plot is selected
                print(f"Selected plot: {selected_item.text()}")
            else:
                # A curve under a plot is selected
                print(f"Selected curve: {selected_item.text()} (under {selected_item.parent().text()})")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    window.setWindowTitle("Time-Series Plotting Application")
    window.resize(1000, 600)
    window.show()

    sys.exit(app.exec())
