# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Qt

class DictView(QWidget):
    def __init__(self, data_dict, parent=None):
        super().__init__(parent)
        self.data_dict = data_dict
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        for key, value in self.data_dict.items():
            row_layout = QHBoxLayout()

            # QLabel for the key
            key_label = QLabel(key)
            key_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(key_label)

            # QLineEdit for the value
            value_edit = QLineEdit(str(value))
            value_edit.textChanged.connect(lambda text, k=key: self.update_dict(k, text))
            row_layout.addWidget(value_edit)

            layout.addLayout(row_layout)

        self.setLayout(layout)

    def update_dict(self, key, value):
        self.data_dict[key] = value
        print(f"Updated {key}: {value}")

if __name__ == "__main__":
    import sys

    # Sample dictionary to be used as the model
    sample_dict = {
        "Name": "John Doe",
        "Age": "30",
        "Email": "john.doe@example.com"
    }

    app = QApplication(sys.argv)
    view = DictView(sample_dict)
    view.show()

    sys.exit(app.exec())
