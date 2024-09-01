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

# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QObject, QStringListModel, Signal, QEvent, QThread
from PySide6.QtWidgets import (
    QLineEdit, QListView, QVBoxLayout, QWidget, QAbstractItemView,
    QLabel
)

from . import menu_filter


class Worker(QThread):
    progress = Signal(int)
    result = Signal(str, list)

    def __init__(self, cmd_fn, kwargs, breadcrumbs):
        super().__init__()
        self.cmd_fn = cmd_fn
        self.kwargs = kwargs
        self.breadcrumbs = breadcrumbs
        self.cancelled = False

    def run(self):
        status, result = self.cmd_fn(self.breadcrumbs, self.progress, **self.kwargs)
        if not self.cancelled:
            self.progress.emit(100)
            self.result.emit(status, result)
        else:
            print("cancelled")

class CommandPalette(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a layout for the command palette
        layout = QVBoxLayout(self)

        self.bc_label = QLabel(self)

        # Create a text input field for command search
        self.command_input = QLineEdit(self)
        self.command_input.setPlaceholderText("Type a command...")

        # Create a list view to display command suggestions
        self.command_list = QListView(self)
        self.command_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.command_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.command_list.setSelectionMode(QAbstractItemView.SingleSelection)

        # Add widgets to layout
        layout.addWidget(self.bc_label)
        layout.addWidget(self.command_input)
        layout.addWidget(self.command_list)

        # Initialize the model
        self.command_model = QStringListModel()
        self.command_list.setModel(self.command_model)

        # Command list for filtering.  key: command name, values: (command_fn, args, kwargs)
        self.commands = {}

        # Most recently used commands and their arguments.  key: command name,
        # value: command arguments
        self.commands_mru = {}

        self.breadcrumbs = []

        # These are the items the palette is currently displaying.  They may
        # differ from the command list when commands return nested sub-commands.
        self.current_items = []

        # A backup of the chosen item in the command list.  This is used to
        # remove the spinner dots when the command is completed.
        self.chosen_item = None

        # Connect the input field to the filtering mechanism
        self.command_input.textChanged.connect(self.filter_commands)

        # Handle command execution when an item is selected
        self.command_list.clicked.connect(self.handle_item_chosen)

        # Initialize the worker
        self.worker = None
        self.old_workers = []
        # self.worker = Worker()
        # FIXME: make signal names consistent with method names
        # self.worker.progress.connect(self.worker_progress)
        # self.worker.result.connect(self.worker_finished)

        self.setFixedSize(400, 300)

        # Install a custom event filter on command_input so that we can catch
        # the Backspace key.
        self.command_input.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.command_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Backspace:
                if self.command_input.text() == "" and self.command_input.cursorPosition() == 0:
                    if len(self.breadcrumbs) > 0:
                        self.go_back()
                        return True
        return super().eventFilter(obj, event)

    def go_back(self):
        """
        Go back to the previous breadcrumb.  Update the bc label and restart the
        worker at the new breadcrumb.
        """
        print("go_back")

        # Clear all list items so that the user can't make a choice before we
        # update the list.
        self.command_model.setStringList([])

        self.breadcrumbs.pop()
        if len(self.breadcrumbs) == 0:
            # We just deleted the top-level breadcrumb, which is the initial
            # command name.  So just show the initial command list.
            self.show()
            return

        # Update the breadcrumb label and restart the worker at the previous
        # level.
        self.bc_label.setText(" > ".join(self.breadcrumbs))
        self.run_chosen_item()

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

    def handle_item_chosen(self, index):
        """
        User has selected a command from the list (by clicking or pressing
        Enter). Execute the selected command.
        """
        # Get the text of the selected item using the supplied index
        self.chosen_item = self.command_model.data(index, Qt.DisplayRole)
        if self.chosen_item is None:
            return

        print(f"palette choice: {self.chosen_item}")

        self.command_input.clear()
        self.breadcrumbs.append(self.chosen_item)
        self.run_chosen_item()

    def run_chosen_item(self):
        print(f'run_chosen_item: {self.breadcrumbs}')
        print(f'mru: {self.commands_mru}')
        # Get the command function from the commands dictionary
        cmd_name = self.breadcrumbs[0]

        # Attempt to load the most recently used breadcrumbs for the command. We
        # consume the mru item to avoid the case where the user uses backspace
        # to go_back() to the previous command which uses the mru again,
        # preventing them from accessing the top-level command list.
        if len(self.breadcrumbs) == 1:
            try:
                self.breadcrumbs = list(self.commands_mru.pop(cmd_name))
            except KeyError:
                pass
            print(f'using mru: {cmd_name}: {self.breadcrumbs}')

        command_fn, kwargs = self.commands[cmd_name]
        self.archive_worker()

        # Scrub any old workers that have finished before creating a new one
        for worker in self.old_workers:
            if worker.isFinished():
                print("removing old worker")
                self.old_workers.remove(worker)

        self.worker = Worker(command_fn, kwargs, self.breadcrumbs)
        self.worker.progress.connect(self.worker_progress)
        self.worker.result.connect(self.worker_finished)

        # Start the worker thread
        self.worker.start()

    def worker_progress(self, value):
        """
        Update the palette with the progress of the currently running command.
        """
        # Update the command list with the progress spinner
        spinner = ["", ".", "..", "..."]
        # progress_text = f"{self.chosen_item} {spinner[value % 4]}"
        progress_text = f"{spinner[value % 4]}"
        # self.command_model.setData(self.command_list.currentIndex(), progress_text)
        self.bc_label.setText(progress_text)

    def worker_finished(self, status, results):
        """
        Update the palette with the results of the command that has finished
        executing.
        """
        print(f'worker_finished: status:{status}, results: {results}')

        # Remove the spinner dots from the current item
        # self.command_model.setData(self.command_list.currentIndex(), self.chosen_item)
        self.bc_label.setText(" > ".join(self.breadcrumbs))

        if status == 'sub-command':
            # Set commands to the results of the sub-command
            self.current_items = results
            self.command_model.setStringList(self.current_items)
            self.command_list.setCurrentIndex(self.command_model.index(0, 0))
        else:
            # The command has completed.  Hide the palette.

            # Save the command and its arguments to the MRU list.  -1 to remove
            # the last breadcrumb, which the user will select again if this
            # command is run.
            print(f'setting mru: {self.breadcrumbs[:-1]}')
            self.commands_mru[self.breadcrumbs[0]] = self.breadcrumbs[:-1]
            self.hide()

    def add_command(self, command_name:str, command_fn:callable, /, **kwargs):
        """
        Add a command to the command palette.

        Args:
            command_name (str): The name of the command.
            command_fn (callable): The function to execute when the command is
                selected.
        """
        self.commands[command_name] = (command_fn, kwargs)

    def set_commands(self, commands:dict):
        """
        Sets commands for the command palette to the given dictionary.
        
        The format of the dictionary is:
        {
            "command_name": (command_fn, args, kwargs),
            ...
        }
        """
        # Store all commands for filtering
        self.commands = commands

    def move_selection_up(self):
        """
        Moves the highlighted selection up in the command list
        """
        print("move_selection_up")
        current_index = self.command_list.currentIndex()
        if current_index.row() > 0:
            self.command_list.setCurrentIndex(
                self.command_model.index(current_index.row() - 1, 0)
                )

    def move_selection_down(self):
        """
        Moves the highlighted selection down in the command list
        """
        print("move_selection_down")
        current_index = self.command_list.currentIndex()
        if current_index.row() < self.command_model.rowCount() - 1:
            self.command_list.setCurrentIndex(
                self.command_model.index(current_index.row() + 1, 0)
                )

    def keyPressEvent(self, event):
        """
        Handles key press events for the command palette
        """
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
            self.handle_item_chosen(index)
        # If ctrl+N is pressed, move the selection down
        elif event.key() == Qt.Key_N and event.modifiers() & Qt.ControlModifier:
            self.move_selection_down()
        # If ctrl+P is pressed, move the selection up
        elif event.key() == Qt.Key_P and event.modifiers() & Qt.ControlModifier:
            self.move_selection_up()
        else:
            super().keyPressEvent(event)

    def hide(self):
        """
        Hides the command palette
        """
        print("palette hide")


        # Reset the command list
        self.command_model.setStringList(self.commands)
        # self.worker.args = []
        # self.worker.clear_context()
        self.breadcrumbs = []
        self.setVisible(False)

    def archive_worker(self):
        """
        Marks the current worker as finished and preserves a reference to it (to
        be cleaned up later).
        """
        # NOTE: The application will crash if we throw away the reference to a
        # running QThread.  So we keep a reference to the old worker threads and
        # discard them when they are finished.
        if self.worker is not None:
            self.worker.cancelled = True
            self.worker.progress.disconnect(self.worker_progress)
            self.worker.result.disconnect(self.worker_finished)
            if self.worker.isRunning():
                self.old_workers.append(self.worker)
            self.worker = None

    def show(self):
        print("palette show")

        # Clear the command input field
        self.command_input.clear()
        self.bc_label.setText("")

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
