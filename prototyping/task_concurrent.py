"""
This script demonstrates how to use the concurrent.futures module to run a
long-running task in a separate thread and update the progress in the main
thread using signals.
"""

import sys
import time
import concurrent.futures

# pylint: disable=no-name-in-module
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QProgressBar, QLabel
)

class Worker(QObject):
    progress = Signal(int)

    def __init__(self):
        super().__init__()
        self.executor = concurrent.futures.ThreadPoolExecutor()

    def start_task(self):
        future = self.executor.submit(self.long_running_task)
        future.add_done_callback(self.task_finished)

    def long_running_task(self):
        for i in range(100):
            time.sleep(0.1)  # Simulate a time-consuming task
            self.progress.emit(i + 1)

    def task_finished(self, _future):
        """
        Callback function that is called when the task is finished
        """
        self.progress.emit(100)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("concurrent.futures Example")
        self.setGeometry(300, 300, 400, 200)

        # Layout and widgets
        self.layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.start_button = QPushButton("Start Task")
        self.status_label = QLabel("Status: Ready")

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.start_button)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # Initialize the worker
        self.worker = Worker()
        self.worker.progress.connect(self.update_progress)

        # Connect button click to start task
        self.start_button.clicked.connect(self.start_task)

    def start_task(self):
        # Disable button to prevent multiple starts
        self.start_button.setEnabled(False)
        self.status_label.setText("Status: Running...")
        self.worker.start_task()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        if value == 100:
            self.status_label.setText("Status: Finished")
            self.start_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
