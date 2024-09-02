"""
This module contains the ProviderManager class.  It is a QMainWindow subclass
that provides a GUI for managing data providers that allows the user to add,
edit, and delete data providers, and test the connection settings for each
provider.
"""

import sys

# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QModelIndex, QAbstractListModel
from PySide6.QtWidgets import QMainWindow, QMenu
from PySide6.QtGui import QAction

from .pyside_ui_loader import load_ui


class ListOfDictModel(QAbstractListModel):
    """
    Model for the table view.  Holds a list of dicts.  Each dict represents a
    provider and has the following keys:

        - name: str
        - provider_type: str
        - config: dict
    
    The keys in the config dict depend on the provider type.
    """
    def __init__(self, parent=None, items:list|None=None, header:str=''):
        super().__init__(parent)
        self._data = items or []
        self.header = header

    def headerData(self, section, orientation, role):
        """
        Returns the header name, which is always 'Provider'.
        """
        if (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
            return self.header
        return super().headerData(section, orientation, role)

    def setData(self, index, value, role=Qt.EditRole):
        """
        Sets model data at the specified index.
        Returns True of the value was successfully assigned.
        """
        if index.isValid() and role == Qt.EditRole:
            # It is assumed that all dicts in _data have a 'name' key
            self._data[index.row()]['name'] = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        return False

    def data(self, index, role=Qt.DisplayRole):
        """
        Returns model data at the specified index.
        """
        if (not index.isValid()) or (role != Qt.DisplayRole):
            return None
        return self._data[index.row()]['name']

    def rowCount(self, _parent):
        """
        Returns the number of rows in the model.
        """
        return len(self._data)

    def flags(self, index):
        """
        Returns flags for the model item at the specified index.  Needed in
        order to make treeview items editable.
        """
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def new(self):
        """
        Adds a new Provider instance to the list of providers in the model.
        """
        name = 'New Provider'
        if name in [x['name'] for x in self._data]:
            idx = 0
            while True:
                num_name = f'{name} ({idx})'
                if num_name not in [x['name'] for x in self._data]:
                    name = num_name
                    break
                idx += 1

        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append({'name': name, 'provider_type': '', 'config': {}})
        self.endInsertRows()

    def delete(self, index):
        """
        Removes the Provider instance from the model's list of providers at
        the specified index.
        """
        self.beginRemoveRows(index, index.row(), index.row())
        self._data.pop(index.row())
        self.endRemoveRows()


class ProviderManager(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        module_root = sys.modules[__name__].__file__
        # It is assumed that the UI file has the same name as the module
        ui_filename = module_root.replace('.py', '.ui')
        load_ui(ui_filename, self)

        # Model for tree view
        self.table_model = ListOfDictModel(parent=self.tree_view, header='Provider')
        # self.table_model.dataChanged.connect(self.data_changed)
        self.tree_view.setModel(self.table_model)

        # Right click tree view
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.clicked.connect(self.row_clicked)

        # Button clicks
        self.save_button.clicked.connect(self.save_clicked)
        self.new_button.clicked.connect(self.new_clicked)
        self.delete_button.clicked.connect(self.delete_clicked)
        self.test_button.clicked.connect(self.test_clicked)
        self.ok_button.clicked.connect(self.ok_clicked)
        self.cancel_button.clicked.connect(self.cancel_clicked)

        self.tree_view.setCurrentIndex(self.table_model.createIndex(0, 0, None))
        # if self.table_model._data:
        #     self.update_view()
        self.update_view()

    def ok_clicked(self):
        self.save_clicked()
        self.hide()

    def cancel_clicked(self):
        self.hide()

    def update_model(self):
        """Copies the values from the widgets into the active provider."""

    def update_view(self):
        """Copy the provider attributes into their respective widgets."""

    def save_clicked(self):
        """
        Called when the save button is clicked.

        Copies all values from the settings tab into the model then writes the
        model to disk.
        """
        # idx = self.tree_view.currentIndex()
        if self.table_model.rowCount(None) == 0:
            self.table_model.new()
            self.tree_view.setCurrentIndex(self.table_model.createIndex(self.table_model.rowCount(None)-1, 0, None))

        self.update_model()

    def row_clicked(self, idx):
        """
        Called when a row is clicked in the tree view.

        Transfers values from the model into the settings tab for the selected
        row.
        """
        self.update_view()

    # def data_changed(self, idx):
    #     """
    #     Not used.
    #     """
    #     print('dc', idx)

    def show_context_menu(self, position):
        """
        Called when user right-clicks on the tree view (provider list).

        Not currently used but could be useful for actions like duplicating a
        provider entry.  Could provide option to rename provider, although this
        is already done via the normal ways of editing a treeview item
        (double-clicking, F2).
        """
        action = QAction("Show Name")
        action.triggered.connect(self.show_name)
        menu = QMenu(self.tree_view)
        menu.addAction(action)
        menu.exec(self.tree_view.mapToGlobal(position))

    def show_name(self):
        """
        Not used except by the context menu above.
        """
        idx = self.tree_view.currentIndex()
        print("item: " + self.table_model.data(idx, Qt.DisplayRole))

    def new_clicked(self):
        """
        Called when user clicks the New button.

        Adds a new Provider to the list with empty settings.
        Highlights the new entry in the provider list.
        """
        self.table_model.new()
        # self.clear_widgets()
        self.tree_view.setCurrentIndex(self.table_model.createIndex(self.table_model.rowCount(None)-1, 0, None))

    def delete_clicked(self):
        """
        Called when user clicks the Delete button.

        Removes the currently selected row from the provider list.
        """
        idx = self.tree_view.currentIndex()
        if idx.row() >= self.table_model.rowCount(None):
            # No row is selected, or no more items to delete.
            return
        self.table_model.delete(idx)

        # If the deleted row was the last row, highlight the row above it so
        # that the user can press the delete button repeatedly in order to
        # remove many items rapidly.
        idx = self.tree_view.currentIndex()
        if idx.row() >= self.table_model.rowCount(None):
            if self.table_model.rowCount(None) > 0:
                self.tree_view.setCurrentIndex(self.table_model.createIndex(self.table_model.rowCount(None)-1, 0, None))

    def test_clicked(self):
        """
        Called when use clicks the Test button.

        Tests the current provider settings (without saving).  Results from
        the test are displayed in the test results area.  The result provides
        an indication to the user about whether the settings are correct.
        """
        hostname = self.hostname_edit.text()
        port = self.port_spin.value()
        username = self.user_edit.text()
        password = self.password_edit.text()

        # self.result_edit.setPlainText(str(result))
