"""
This module contains the ProviderManager class.  It is a QMainWindow subclass
that provides a GUI for managing data providers that allows the user to add,
edit, and delete data providers, and test the connection settings for each
provider.
"""

import dataclasses
import json
import os
import sys

# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QModelIndex, QAbstractListModel
from PySide6.QtWidgets import QMainWindow, QMenu
from PySide6.QtGui import QAction

from .pyside_ui_loader import load_ui

CFG_FILENAME = 'provider_config.json'
DEFAULT_CFG = {'providers': []}

@dataclasses.dataclass
class Provider:
    """Data provider"""
    name: str
    provider_type: str = ''
    hostname: str = ''
    username: str = ''
    password: str = ''
    port: int = 0

def json_load_objhook(obj):
    """
    Called by json.load for each object loaded, if obj is a dict with key
    'providers', replaces the value for that key with a list of Provider
    instances.  It effectively allows us to load a list of objects (not just a
    dict) from a json config file.
    """
    if isinstance(obj, dict):
        if 'providers' in obj:
            providers = []
            for provider_dict in obj['providers']:
                provider = Provider(**provider_dict)
                providers.append(provider)
            obj['providers'] = providers

    return obj

def load_cfg(infilename) -> list:
    """
    Loads the program configuration file from json.
    """
    if os.path.exists(infilename):
        with open(infilename, 'r', encoding='utf-8') as infile:
            cfg = json.load(infile, object_hook=json_load_objhook)
    else:
        cfg = DEFAULT_CFG
    return cfg

class ProviderJSONEncoder(json.JSONEncoder):
    """
    Subclass of JSONEncoder that supports writing dataclass instances as json
    dicts.  Used in this application to save lists of Provider instances to
    disk.
    """
    def default(self, o):
        if isinstance(o, Provider):
            return dataclasses.asdict(o)
        return super().default(o)

def save_cfg(outfilename, providers):
    """
    Write the program configuration file to disk in .json format.
    """
    cfg = {'providers': providers}
    with open(outfilename, 'w', encoding='utf-8') as outfile:
        json.dump(cfg, outfile, cls=ProviderJSONEncoder, indent=4)

class TableModel(QAbstractListModel):
    """
    Model for the table view.  Holds a list of Provider instances.
    """
    def __init__(self, parent=None, providers=None):
        super().__init__(parent=parent)
        self.providers = [] if providers is None else providers

    def headerData(self, section, orientation, role):
        """
        Returns the header name
        """
        if (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
            return "Provider"
        return super().headerData(section, orientation, role)

    def setData(self, idx, value, role=Qt.EditRole):
        """
        Sets model data at the specified index.
        Returns True of the value was successfully assigned.
        """
        if not value:
            # Don't allow setting name to ''
            return False

        if value in self.providers:
            # Don't allow duplicates
            return False

        if role == Qt.EditRole:
            # print('sd:', idx.row(), value)
            # self.providers[idx.row()] = Provider(name=value)
            self.providers[idx.row()].name=value
            return True
        return False

    def data(self, idx, role=Qt.DisplayRole):
        """
        Returns model data at the specified index.
        """
        if role == Qt.DisplayRole:
            return self.providers[idx.row()].name

    def rowCount(self, _parent):
        """
        Returns the number of rows in the model.
        """
        return len(self.providers)

    def flags(self, idx):
        """
        Returns flags for the model item at the specified index.  Needed in
        order to make treeview items editable.
        """
        return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def new(self):
        """
        Adds a new Provider instance to the list of providers in the model.
        """
        name = 'New Provider'
        if name in [x.name for x in self.providers]:
            idx = 0
            while True:
                num_name = f'{name} ({idx})'
                if num_name not in [x.name for x in self.providers]:
                    name = num_name
                    break
                idx += 1

        self.beginInsertRows(QModelIndex(), len(self.providers), len(self.providers))
        self.providers.append(Provider(name=name))
        self.endInsertRows()

    def delete(self, idx):
        """
        Removes the Provider instance from the model's list of providers at
        the specified index.
        """
        self.beginRemoveRows(idx, idx.row(), idx.row())
        self.providers.pop(idx.row())
        self.endRemoveRows()

class ProviderManager(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        module_root = sys.modules[__name__].__file__
        # It is assumed that the UI file has the same name as the module
        ui_filename = module_root.replace('.py', '.ui')
        load_ui(ui_filename, self)

        cfg = load_cfg(CFG_FILENAME)

        # Model for tree view
        self.table_model = TableModel(parent=self.tree_view, providers=cfg['providers'])
        # self.table_model.dataChanged.connect(self.data_changed)
        self.tree_view.setModel(self.table_model)

        # Right click tree view
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.clicked.connect(self.row_clicked)

        # Button clicks
        self.save_button.clicked.connect(self.save)
        self.new_button.clicked.connect(self.new_clicked)
        self.delete_button.clicked.connect(self.delete_clicked)
        self.test_button.clicked.connect(self.test_clicked)
        self.ok_button.clicked.connect(self.ok_clicked)
        self.cancel_button.clicked.connect(self.cancel_clicked)

        self.tree_view.setCurrentIndex(self.table_model.createIndex(0, 0, None))
        if self.table_model.providers:
            self.copy_model_values_to_widgets()

    def ok_clicked(self):
        self.save()
        self.hide()

    def cancel_clicked(self):
        self.hide()

    def copy_widget_values_to_model(self):
        """Copies the values from the widgets into the active provider."""
        idx = self.tree_view.currentIndex()
        prov = self.table_model.providers[idx.row()]

        prov.provider_type = self.type_combo.currentText()
        prov.hostname = self.hostname_edit.text()
        prov.port = self.port_spin.value()
        prov.username = self.user_edit.text()
        prov.password = self.password_edit.text()

    def copy_model_values_to_widgets(self):
        """Copy the provider attributes into their respective widgets."""
        idx = self.tree_view.currentIndex()
        try:
            prov = self.table_model.providers[idx.row()]
        except IndexError:
            # print(f"ERROR: No provider at idx {idx.row()}")
            return

        combo_idx = self.type_combo.findText(prov.provider_type)
        if combo_idx == -1:
            self.type_combo.setCurrentText(f'Unknown ({prov.provider_type})')
            print(f"ERROR: Unknown provider type '{prov.provider_type}'")
            return

        self.type_combo.setCurrentIndex(combo_idx)
        self.hostname_edit.setText(prov.hostname)
        self.port_spin.setValue(prov.port)
        self.user_edit.setText(prov.username)
        self.password_edit.setText(prov.password)

    def clear_widgets(self):
        """Clears all widget values."""
        self.type_combo.setCurrentIndex(0)
        self.hostname_edit.setText('')
        self.port_spin.setValue(0)
        self.user_edit.setText('')
        self.password_edit.setText('')

    def save(self):
        """
        Called when the save button is clicked.

        Copies all values from the settings tab into the model then writes the
        model to disk.
        """
        # idx = self.tree_view.currentIndex()
        if len(self.table_model.providers) == 0:
            self.table_model.new()
            self.tree_view.setCurrentIndex(self.table_model.createIndex(len(self.table_model.providers)-1, 0, None))

        self.copy_widget_values_to_model()
        save_cfg(CFG_FILENAME, self.table_model.providers)

    def row_clicked(self, idx):
        """
        Called when a row is clicked in the tree view.

        Transfers values from the model into the settings tab for the selected
        row.
        """
        self.copy_model_values_to_widgets()

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
        self.clear_widgets()
        self.tree_view.setCurrentIndex(self.table_model.createIndex(len(self.table_model.providers)-1, 0, None))

    def delete_clicked(self):
        """
        Called when user clicks the Delete button.

        Removes the currently selected row from the provider list.
        """
        idx = self.tree_view.currentIndex()
        if idx.row() >= len(self.table_model.providers):
            # No row is selected, or no more items to delete.
            return
        self.table_model.delete(idx)

        # If the deleted row was the last row, highlight the row above it so
        # that the user can press the delete button repeatedly in order to
        # remove many items rapidly.
        idx = self.tree_view.currentIndex()
        if idx.row() >= len(self.table_model.providers):
            if len(self.table_model.providers) > 0:
                self.tree_view.setCurrentIndex(self.table_model.createIndex(len(self.table_model.providers)-1, 0, None))

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
