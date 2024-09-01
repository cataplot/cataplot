"""
This module provides a command palette widget that can be used to execute
commands in the application. The command palette is a searchable list of
commands that can be executed by selecting them from the list, and is similar in
appearance and behavior to those found in Sublime Text, VS Code, and other
applications. The command palette can be shown by pressing a keyboard shortcut
(controlled by the application), and hidden by pressing the Escape key.

This palette implementation is designed to support commands that don't complete
immediately.  In such cases, the palette will show a spinner (in the form ., ..,
... cycling in the command list) to indicate that the command is still running.

In order to keep the user interface responsive, commands are executed in a
separate thread.  This is done using the `concurrent.futures` module, which
provides a high-level interface for asynchronously executing functions in
separate threads.

The CommandPalette class provides methods for registering commands.

"""
import concurrent.futures

# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QObject, QStringListModel, Signal
from PySide6.QtWidgets import (
    QLineEdit, QListView, QVBoxLayout, QWidget, QAbstractItemView
)

from . import menu_filter


class Worker(QObject):
    progress = Signal(int)
    result = Signal(str, list)

    def __init__(self):
        super().__init__()
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.command_fn = None
        self.command_args = []

    def start_task(self):
        """
        Start the task in a separate thread
        """
        future = self.executor.submit(self.command_fn, self.command_args,
                                      self.progress)

        future.add_done_callback(self.task_finished)

    def task_finished(self, future):
        """
        Callback function that is called when the task is finished
        """
        self.progress.emit(100)
        status, results = future.result()
        print(f'task_finished: status:{status}, results:{results}')

        # Reset the command args and function if the command is completed
        if status == 'completed':
            self.command_args = []
            self.command_fn = None

        self.result.emit(status, results)

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

        # Command list for filtering.  key: command name, value: command fn
        self.commands = {}

        # Most recently used commands and their arguments.  key: command name,
        # value: command arguments
        self.commands_mru = {}

        # These are the items the palette is currently displaying.  They may
        # differ from the command list when commands return nested sub-commands.
        self.current_items = []

        # A backup of the chosen item in the command list.  This is used to
        # remove the spinner dots when the command is completed.
        self.chosen_item = None

        # Connect the input field to the filtering mechanism
        self.command_input.textChanged.connect(self.filter_commands)

        # Handle command execution when an item is selected
        self.command_list.clicked.connect(self.execute_item)

        # Initialize the worker
        self.worker = Worker()
        self.worker.progress.connect(self.worker_progress)
        self.worker.result.connect(self.worker_finished)

        self.setFixedSize(400, 300)

    def filter_commands(self, text):
        print(f"filter_commands: {text}")
        # print(self.commands)
        # print(self.current_items)
        # print(self.command_model.stringList())

        filtered = menu_filter.filter_list(text, self.current_items)

        # Update the model with the filtered commands
        self.command_model.setStringList(filtered)

        # Highlight the first item in the list
        if filtered:
            self.command_list.setCurrentIndex(self.command_model.index(0, 0))

    def execute_item(self, index):
        """
        User has selected a command from the list (by clicking or pressing
        Enter). Execute the selected command.
        """
        # Get the selected command
        self.chosen_item = self.command_model.data(index, Qt.DisplayRole)
        if self.chosen_item is None:
            return

        self.command_input.clear()
        self.worker.command_args.append(self.chosen_item)

        print(f"palette choice: {self.chosen_item}")

        # Get the command function from the commands dictionary
        command_fn = self.commands[self.worker.command_args[0]]

        # Set the command function in the worker
        self.worker.command_fn = command_fn

        # Start the worker thread
        self.worker.start_task()

    def worker_progress(self, value):
        """
        Update the palette with the progress of the currently running command.
        """
        # Update the command list with the progress spinner
        spinner = ["", ".", "..", "..."]
        progress_text = f"{self.chosen_item} {spinner[value % 4]}"
        self.command_model.setData(self.command_list.currentIndex(), progress_text)

    def worker_finished(self, status, results):
        """
        Update the palette with the results of the command that has finished
        executing.
        """
        print(f'worker_finished: status:{status}, results: {results}')

        # Remove the spinner dots from the current item
        self.command_model.setData(self.command_list.currentIndex(), self.chosen_item)

        if status == 'sub-command':
            # Set commands to the results of the sub-command
            self.current_items = results
            self.command_model.setStringList(self.current_items)
            self.command_list.setCurrentIndex(self.command_model.index(0, 0))
        else:
            self.hide()

    def add_command(self, command_name:str, command_fn:callable):
        """
        Add a command to the command palette.

        Args:
            command_name (str): The name of the command.
            command_fn (callable): The function to execute when the command is
                selected.
        """
        self.commands[command_name] = command_fn

    def set_commands(self, commands:dict):
        """
        Sets commands for the command palette to the given dictionary.
        """
        # Store all commands for filtering
        self.commands = commands

    def move_selection_up(self):
        print("move_selection_up")
        current_index = self.command_list.currentIndex()
        if current_index.row() > 0:
            self.command_list.setCurrentIndex(
                self.command_model.index(current_index.row() - 1, 0)
                )

    def move_selection_down(self):
        print("move_selection_down")
        current_index = self.command_list.currentIndex()
        if current_index.row() < self.command_model.rowCount() - 1:
            self.command_list.setCurrentIndex(
                self.command_model.index(current_index.row() + 1, 0)
                )

    def keyPressEvent(self, event):
        # Hide the palette if the Escape key is pressed
        if event.key() == Qt.Key_Escape:
            self.hide()
        # If the Up key is pressed, move the selection up
        elif event.key() == Qt.Key_Up:
            self.move_selection_up()
        # If the Down key is pressed, move the selection down
        elif event.key() == Qt.Key_Down:
            self.move_selection_down()
        # If the Enter key is pressed, execute the selected command and close the palette
        elif event.key() == Qt.Key_Return:
            index = self.command_list.currentIndex()
            self.execute_item(index)
        # If ctrl+N is pressed, move the selection down
        elif event.key() == Qt.Key_N and event.modifiers() & Qt.ControlModifier:
            self.move_selection_down()
        # If ctrl+P is pressed, move the selection up
        elif event.key() == Qt.Key_P and event.modifiers() & Qt.ControlModifier:
            self.move_selection_up()
        else:
            super().keyPressEvent(event)

    def hide(self):
        print("palette hide")

        # Reset the command list
        self.command_model.setStringList(self.commands)
        self.worker.command_args = []
        self.setVisible(False)

    def show(self):
        print("palette show")

        # Clear the command input field
        self.command_input.clear()

        # Populate current items from commands
        self.current_items = self.commands.keys()
        self.command_model.setStringList(self.current_items)

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
