"""
Example of how to use QThread to run a time-consuming task in a separate thread
and update the progress in the main thread.
"""

import sys
import time

# pylint: disable=no-name-in-module
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QProgressBar, QLabel

class WorkerThread(QThread):
    # Signal to update progress in the main thread
    progress_updated = Signal(int)

    def run(self):
        for i in range(100):
            time.sleep(0.1)  # Simulate a time-consuming task
            self.progress_updated.emit(i + 1)  # Emit progress signal

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("QThread Example")
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

        # Connect button click to start task
        self.start_button.clicked.connect(self.start_task)

        # Initialize the worker thread
        self.worker_thread = WorkerThread()
        self.worker_thread.progress_updated.connect(self.update_progress)

    def start_task(self):
        # Disable button to prevent multiple starts
        self.start_button.setEnabled(False)
        self.status_label.setText("Status: Running...")

        # Start the worker thread
        self.worker_thread.start()

        # Connect the thread finished signal to update the UI
        self.worker_thread.finished.connect(self.task_finished)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def task_finished(self):
        self.status_label.setText("Status: Finished")
        self.start_button.setEnabled(True)
        self.progress_bar.setValue(100)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
