"""
Mock-up of a time-series plotting application using PySide6 and pyqtgraph using
a model / view architecture.
"""

import sys

# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QModelIndex, QPoint
from PySide6.QtWidgets import (QApplication, QMainWindow, QSplitter, QTreeView,
                               QVBoxLayout, QWidget, QMenu, QInputDialog,
                               QMessageBox)
from PySide6.QtGui import QStandardItemModel, QStandardItem

import pyqtgraph as pg

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

        # Set up context menu for the tree view
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.open_context_menu)

        # Connect the tree view to handle selections
        self.tree_view.selectionModel().currentChanged.connect(self.on_tree_selection_changed)

        # Enable double-click to edit the plot names in place
        self.tree_view.setEditTriggers(QTreeView.DoubleClicked | QTreeView.EditKeyPressed)

        self.model.dataChanged.connect(self.on_item_changed)

    def on_item_changed(self, top_left: QModelIndex, bottom_right: QModelIndex):
        """Update the pyqtgraph plot title when an item in the tree view is renamed."""
        item = self.model.itemFromIndex(top_left)
        
        # Check if the item is a plot (parent is None)
        if item and item.parent() is None:
            plot_index = top_left.row()  # Get the index of the plot
            new_plot_name = item.text()  # Get the new plot name
            
            # Update the corresponding plot's title in the PlotManager
            plot_widget = self.plot_manager.plots[plot_index]
            plot_widget.setTitle(new_plot_name)


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

    def open_context_menu(self, position: QPoint):
        """Create and open the context menu when right-clicking on the tree view."""
        indexes = self.tree_view.selectedIndexes()
        selected_item = self.model.itemFromIndex(indexes[0]) if indexes else None

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
            plot_item = self.model.add_plot(plot_name)
            # Add to plot manager
            self.plot_manager.add_plot(plot_name)

    def rename_plot(self, plot_item):
        """Rename an existing plot by entering inline edit mode."""
        # Get the QModelIndex for the plot item
        index = self.model.indexFromItem(plot_item)
        
        # Programmatically trigger edit mode in the QTreeView
        self.tree_view.edit(index)

    def delete_plot(self, plot_item):
        """Delete a plot from the model and the plot manager."""
        reply = QMessageBox.question(self, 'Delete Plot', f"Are you sure you want to delete '{plot_item.text()}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Find the index of the plot in the model
            index = self.model.indexFromItem(plot_item).row()
            # Remove from plot manager
            self.plot_manager.remove_plot(index)
            # Remove from model
            self.model.removeRow(index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MainWindow()
    window.setWindowTitle("Time-Series Plotting Application with Inline Editing")
    window.resize(1000, 600)
    window.show()
    
    sys.exit(app.exec())
