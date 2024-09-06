"""
Demonstrates how to create a time series plot that fetches more data when the
user pans to the edge of the available data.
"""
import time
import sys

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer
import pyqtgraph as pg
import numpy as np

import numpy as np

def generate_data(xmin: float, xmax: float, grid:float=0.1,
                  align:str='center') -> tuple[np.ndarray, np.ndarray]:
    """
    Generates example data for the given x range. The function we generate is
    sin(x), and we only generate data points for x values in the given range
    that are multiples of 0.1.
    
    Parameters:
        xmin (float): The minimum x value
        
        xmax (float): The maximum x value

        grid (float): The alignment of the x values.  The x values are
        generated in increments of this value.  The default is 0.1.

        align (str):
        
    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing the x values and the
        corresponding sin(x) values.
    """
    if align == 'right':
        # Round xmin up to the nearest multiple of grid
        xmin = np.ceil(xmin / grid) * grid
    elif align == 'left':
        xmax = np.floor(xmax / grid) * grid
    elif align == 'center':
        xmin = np.ceil(xmin / grid) * grid
        xmax = np.floor(xmax / grid) * grid

    x_values = np.arange(xmin, xmax, grid)
    y_values = np.sin(x_values)

    # if x_values.any():
    #     print(f"Generated data for x range [{x_values[0]}, {x_values[-1]}]")

    return x_values, y_values


def get_needed_x_range(old_x_range:tuple[float, float],
                       new_x_range:tuple[float, float]
                       ) -> list[tuple[float, float]]:
    """
    Given the old x range and the new x range, return the x range(s) that needs
    to be fetched in order to fill the gap.

    Example: User zooms out and the current view range is [-100, 100].  The
    previous view range was [0, 50].  This function would return [[-100, 0],
    [50, 100]].  The caller can then fetch data for those x ranges.

    Format of new_x_range parameters: [x_min, x_max]
    """
    ranges = []
    # Is the new view range x minimum less than the previous view range x
    # minimum?
    if new_x_range[0] < old_x_range[0]:
        ranges.append([new_x_range[0], old_x_range[0]])

    # Is the new view range x maximum greater than the previous view range x
    # maximum?
    if new_x_range[1] > old_x_range[1]:
        ranges.append([old_x_range[1], new_x_range[1]])

    return ranges


class TimeSeriesPlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create layout and plot widget
        layout = QVBoxLayout(self)
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        # Generate initial time-series data
        # self.x = np.linspace(0, 100, 1000)
        # self.y = np.sin(self.x)
        self.x, self.y = generate_data(0, 5, align='right', grid=.3)

        # Plot the initial data.  Show dots at each data point.
        self.plot = self.plot_widget.plot(self.x, self.y, pen=None, symbol='o')

        # Connect to the signal emitted when the user pans or zooms
        self.plot_widget.getViewBox().sigRangeChanged.connect(self.on_view_range_changed)

        # Capture the initial view range so that we can detect when the user
        # pans to the edge of the available data
        self.view_range = self.plot_widget.getViewBox().viewRange()

        self.tmp_counter = 0

        self.last_range_change_time = time.monotonic()
        self.timer = None
        self.deferred_range = None

    def on_timer(self):
        self.timer.stop()
        self.timer = None
        # self.on_view_range_changed(None, self.deferred_range, deferred=True)
        self.update_data_for_new_range(self.deferred_range)


    def update_data_for_new_range(self, view_range):
        self.x, self.y = generate_data(view_range[0][0],
                                       view_range[0][1],
                                       align='right',
                                       grid=.3)
        # Update the plot with the new data
        self.plot.setData(self.x, self.y)

    def on_view_range_changed(self, _view_box, view_range):
        """
        view_range format: [[x_min, x_max], [y_min, y_max]]
        """
        now = time.monotonic()
        # Called as a result of a user interaction with the plot
        dt = now - self.last_range_change_time
        if (dt) < 0.1:
            # It hasn't been long enough since the last range change.  Defer the
            # update until later (to avoid fetching data quite so often) using
            # a QTimer.
            if self.timer is not None:
                self.timer.stop()
            self.timer = QTimer()
            self.timer.timeout.connect(self.on_timer)
            self.timer.start(100)  # 100 ms
            self.deferred_range = view_range
            return

        self.last_range_change_time = now

        self.update_data_for_new_range(view_range)

        # self.tmp_counter += 1
        # print('tmp_counter', self.tmp_counter)
        # # Get the x range that needs to be fetched
        # needed_ranges = get_needed_x_range(self.view_range[0], view_range[0])

        # # Fetch the needed data
        # for needed_range in needed_ranges:
        #     new_x, new_y = generate_data(needed_range[0], needed_range[1])
        #     # Determine whether the new data goes to the left or right of the
        #     # existing data
        #     if needed_range[0] < self.x[0]:
        #         self.x = np.concatenate([new_x, self.x])
        #         self.y = np.concatenate([new_y, self.y])
        #     else:
        #         self.x = np.concatenate([self.x, new_x])
        #         self.y = np.concatenate([self.y, new_y])

        # self.x, self.y = generate_data(view_range[0][0],
        #                                view_range[0][1],
        #                                align='right',
        #                                grid=.3)

        # # print(f'len(self.x): {len(self.x)}')

        # # Update the view range
        # self.view_range = view_range

        # # Update the plot with the new data
        # self.plot.setData(self.x, self.y)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create and set central widget
        self.central_widget = TimeSeriesPlot(self)
        self.setCentralWidget(self.central_widget)

        # Set window title and geometry
        self.setWindowTitle("Time Series Plot with Data Fetching")
        self.setGeometry(100, 100, 800, 600)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
