from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)
from qgis.core import Qgis


class ConfigDialog(QDialog):
    """Set path to GFLOW executable."""

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("Configure GFLOW")
        self.install_task = None

        # Define widgets
        self.browse_button = QPushButton("Browse...")
        self.set_button = QPushButton("Set")
        self.path_line_edit = QLineEdit()
        self.path_line_edit.setMinimumWidth(400)
        self.close_button = QPushButton("Close")

        # Connect with actions
        self.browse_button.clicked.connect(self.set_path)
        self.set_button.clicked.connect(self.store_exe_path)
        self.close_button.clicked.connect(self.reject)

        # Set layout
        exe_row = QHBoxLayout()
        exe_row.addWidget(QLabel("GFLOW executable"))
        exe_row.addWidget(self.path_line_edit)
        exe_row.addWidget(self.browse_button)
        exe_row.addWidget(self.set_button)

        zip_group = QGroupBox("Set GFLOW executable")
        zip_group.setLayout(exe_row)

        path = self.parent.get_gflow_path()
        if path is not None:
            self.path_line_edit.setText(path)

        layout = QVBoxLayout()
        layout.addWidget(zip_group)
        layout.addWidget(self.close_button, stretch=0, alignment=Qt.AlignRight)
        layout.addStretch()
        self.setLayout(layout)

    def set_path(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select file", "", "*")
        if path != "":  # Empty string in case of cancel button press
            self.path_line_edit.setText(path)
        return

    def store_exe_path(self) -> None:
        path = self.path_line_edit.text()
        if path == "":
            return
        if not Path(path).exists():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Invalid GFLOW executable path")
            msg.setText("Could not find GFLOW executable at the provided path!")
            msg.exec_()
            return

        self.parent.set_gflow_path(path)
        self.parent.message_bar.pushMessage(
            title="Info",
            text=f"Succesfully stored GFLOW executable path: {path}",
            level=Qgis.Info,
        )
        return
