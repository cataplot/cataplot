"""
PySide6 Tab Widget with Context Menu Example

This application demonstrates the use of QTabWidget and QTreeView together with
a context menu to allow tab management functionality. The key features of the
application are:
 - A QTabWidget that displays multiple tabs, each associated with a simple
   QWidget.
 - A QTreeView that displays the names of the tabs in a tree structure, which is
   editable.
 - Synchronization between the QTabWidget and QTreeView, where any changes to
   tab names in either widget are reflected in the other.
 - A context menu (right-click) on the QTabWidget's tab bar that provides three
   actions:
  - Add Tab: Adds a new tab with a default name ("Tab X") at the end of the tab
    list.
  - Delete Tab: Deletes the selected tab (but always leaves at least one tab
    remaining).
  - Rename Tab: Allows the user to edit the name of the selected tab.

Key functionalities:
 - Double-clicking a tab allows for inline editing of the tab name.
 - Changes to the tab names are reflected in the QTreeView and the internal list
   of tab names.
 - Selecting a tab in the QTreeView switches the current tab in the QTabWidget.
 - A right-click context menu on the tabs provides options to add, delete, or
   rename tabs.
 - Tabs can be reordered by dragging them in the QTabWidget, and the order is
   reflected in the QTreeView.

Usage:
 - Launch the application and use the tree view or tabs to navigate.
 - Right-click on a tab to open the context menu for managing tabs.
"""


import sys

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QTreeView, QTabWidget,
    QWidget, QVBoxLayout, QLabel, QMenu
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction
from PySide6.QtCore import Qt



class TreeModel(QStandardItemModel):
    def __init__(self, tabs, parent=None):
        super().__init__(parent)

        # Set header label
        self.setHorizontalHeaderLabels(['Tabs'])

        # Add items representing the tabs
        for tab_name in tabs:
            item = QStandardItem(tab_name)
            item.setEditable(True)  # Enable editing of tab names
            self.appendRow(item)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TreeView and TabWidget Example")
        self.setGeometry(100, 100, 600, 400)

        # Create a QSplitter
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Horizontal)

        # Create a QTreeView on the left
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)  # Hide the header for simplicity
        splitter.addWidget(self.tree_view)

        # Create a QTabWidget on the right
        self.tab_widget = TabWidget(self)
        splitter.addWidget(self.tab_widget)

        # Create tab names and initialize the TreeModel with them
        self.tabs = ["Tab 1", "Tab 2", "Tab 3"]
        self.tree_model = TreeModel(self.tabs)
        self.tree_view.setModel(self.tree_model)

        # Add tabs to the QTabWidget
        for tab_name in self.tabs:
            tab_content = self.create_tab(tab_name)
            self.tab_widget.addTab(tab_content, tab_name)

        # Set splitter as the central widget
        self.setCentralWidget(splitter)

        # Connect the tree view selection to change the tab
        self.tree_view.selectionModel().selectionChanged.connect(self.on_tree_selection)

        # Connect the tree model to track when the user edits a tab name
        self.tree_model.itemChanged.connect(self.on_item_changed)

    def move_tab(self, from_index, to_index):
        """Reorders the tabs and updates the tree view accordingly."""
        # Move the tab name in the internal tabs list
        self.tabs.insert(to_index, self.tabs.pop(from_index))

        # Move the corresponding item in the tree model
        item = self.tree_model.takeRow(from_index)
        self.tree_model.insertRow(to_index, item)

    def create_tab(self, tab_name):
        """Creates a simple QWidget containing a label for each tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(f"This is {tab_name}")
        layout.addWidget(label)
        widget.setLayout(layout)
        return widget

    def on_tree_selection(self, selected, deselected):
        """Handles selection in the tree view and changes the tab."""
        indexes = selected.indexes()
        if indexes:
            index = indexes[0]
            tab_name = self.tree_model.itemFromIndex(index).text()
            # Find the index of the tab by name and set it as current
            tab_index = self.tabs.index(tab_name)
            self.tab_widget.setCurrentIndex(tab_index)

    def on_item_changed(self, item):
        """Handles the event when an item in the tree view is edited."""
        new_tab_name = item.text()
        tab_index = self.tree_model.indexFromItem(item).row()

        # Update the corresponding tab's title in QTabWidget
        self.tab_widget.setTabText(tab_index, new_tab_name)

        # Update the name in the internal tabs list
        self.tabs[tab_index] = new_tab_name

    def add_tab(self):
        """
        Adds a new tab.  Names it "Tab X" where X is the next number in the
        sequence that is not already used.
        """
        for i in range(1, len(self.tabs) + 2):
            new_tab_name = f"Tab {i}"
            if new_tab_name not in self.tabs:
                break
        self.tabs.append(new_tab_name)

        # Add a new item to the tree view model
        item = QStandardItem(new_tab_name)
        item.setEditable(True)
        self.tree_model.appendRow(item)

        # Add a new tab to the QTabWidget
        new_tab_content = self.create_tab(new_tab_name)
        self.tab_widget.addTab(new_tab_content, new_tab_name)

    def delete_tab(self, index):
        """Deletes the tab at the given index."""
        if len(self.tabs) > 1:  # Ensure at least one tab remains
            # Remove the tab from the tab widget and tree model
            self.tab_widget.removeTab(index)
            self.tree_model.removeRow(index)
            del self.tabs[index]

    def edit_tree_item_from_tab(self, tab_index):
        """Put the corresponding tree view item into edit mode based on the tab index."""
        tree_index = self.tree_model.index(tab_index, 0)  # Get the index in the tree view model
        self.tree_view.edit(tree_index)  # Start editing that item in the tree view


class TabWidget(QTabWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # Enable tab reordering by dragging
        self.setMovable(True)

        self.tabBarDoubleClicked.connect(self.edit_tab_name)

        # Connect the tab moved signal
        self.tabBar().tabMoved.connect(self.on_tab_moved)

    def on_tab_moved(self, from_index, to_index):
        """Handles the event when a tab is moved by the user."""
        self.main_window.move_tab(from_index, to_index)

    def edit_tab_name(self, index):
        """Start editing the tab name when double-clicked."""
        self.main_window.edit_tree_item_from_tab(index)

    def contextMenuEvent(self, event):
        """Handle right-click context menu for tabs."""
        # Get the index of the tab under the mouse
        tab_index = self.tabBar().tabAt(event.pos())

        menu = QMenu(self)

        # Add "Add Tab" action
        add_action = QAction("Add Tab", self)
        add_action.triggered.connect(self.main_window.add_tab)
        menu.addAction(add_action)

        # Add "Delete Tab" action (only if there are more than one tab)
        if tab_index != -1:
            delete_action = QAction("Delete Tab", self)
            delete_action.triggered.connect(lambda: self.main_window.delete_tab(tab_index))
            menu.addAction(delete_action)

        # Add "Rename Tab" action (only if a valid tab is clicked)
        if tab_index != -1:
            rename_action = QAction("Rename Tab", self)
            rename_action.triggered.connect(lambda: self.edit_tab_name(tab_index))
            menu.addAction(rename_action)

        # Show the context menu at the cursor position
        menu.exec(event.globalPos())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
