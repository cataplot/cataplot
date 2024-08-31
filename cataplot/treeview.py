"""
Subclass of QTreeView with a size hint to set the initial width.
"""
# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QTreeView

class TreeView(QTreeView):
    def sizeHint(self):
        size = super().sizeHint()
        # NB: Percent
        size.setWidth(20)
        return size
