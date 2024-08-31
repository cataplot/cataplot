"""
This module contains the implementation of the command palette widget.
"""

# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtWidgets import (
    QLineEdit, QListView, QVBoxLayout, QWidget, QAbstractItemView
)

from . import menu_filter

class CommandPalette(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a layout for the command palette
        layout = QVBoxLayout(self)

        # Create a text input field for command search
        self.command_input = QLineEdit(self)
        self.command_input.setPlaceholderText("Type a command...")

        # Create a list view to display command suggestions
        self.command_list = QListView(self)
        self.command_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.command_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.command_list.setSelectionMode(QAbstractItemView.SingleSelection)

        # Add widgets to layout
        layout.addWidget(self.command_input)
        layout.addWidget(self.command_list)

        # Initialize the model
        self.command_model = QStringListModel()
        self.command_list.setModel(self.command_model)

        # Command list for filtering
        self.all_commands = []

        # Connect the input field to the filtering mechanism
        self.command_input.textChanged.connect(self.filter_commands)

        # Handle command execution when an item is selected
        self.command_list.clicked.connect(self.execute_command)

        self.setFixedSize(400, 300)

    def filter_commands(self, text):
        filtered = menu_filter.filter_list(text, self.all_commands)

        # Update the model with the filtered commands
        self.command_model.setStringList(filtered)

        # Highlight the first item in the list
        if filtered:
            self.command_list.setCurrentIndex(self.command_model.index(0, 0))

    def execute_command(self, index):
        # Get the selected command
        selected_command = self.command_model.data(index, Qt.DisplayRole)

        # FIXME: map this to actual functionality here
        print(f"Executing command: {selected_command}")
        self.setVisible(False)

        if selected_command == "Add Plot Item":
            self.set_commands(['serverA', 'serverB'])
            self.show()

    def set_commands(self, commands):
        # Store all commands for filtering
        self.all_commands = commands
        # Initially show all commands
        self.command_model.setStringList(commands)

    def move_selection_up(self):
        current_index = self.command_list.currentIndex()
        if current_index.row() > 0:
            self.command_list.setCurrentIndex(
                self.command_model.index(current_index.row() - 1, 0)
                )

    def move_selection_down(self):
        current_index = self.command_list.currentIndex()
        if current_index.row() < self.command_model.rowCount() - 1:
            self.command_list.setCurrentIndex(
                self.command_model.index(current_index.row() + 1, 0)
                )

    def keyPressEvent(self, event):
        # Hide the palette if the Escape key is pressed
        if event.key() == Qt.Key_Escape:
            self.setVisible(False)
        # If the Up key is pressed, move the selection up
        elif event.key() == Qt.Key_Up:
            self.move_selection_up()
        # If the Down key is pressed, move the selection down
        elif event.key() == Qt.Key_Down:
            self.move_selection_down()
        # If the Enter key is pressed, execute the selected command and close the palette
        elif event.key() == Qt.Key_Return:
            self.execute_command(self.command_list.currentIndex())

        # If ctrl+N is pressed, move the selection down
        elif event.key() == Qt.Key_N and event.modifiers() & Qt.ControlModifier:
            self.move_selection_down()
        # If ctrl+P is pressed, move the selection up
        elif event.key() == Qt.Key_P and event.modifiers() & Qt.ControlModifier:
            self.move_selection_up()
        else:
            super().keyPressEvent(event)

    def show(self):
        # Clear the command input field
        self.command_input.clear()

        # Highlight the first item in the list
        if self.command_model.rowCount() > 0:
            self.command_list.setCurrentIndex(
                self.command_model.index(0, 0)
            )

        self.setVisible(True)
        self.command_input.setFocus()

        # Horizontally center the palette in the main window.  Leave
        # vertical position as is.
        x = self.parent().width() / 2 - self.width() / 2
        y = self.y()
        self.move(x, y)
