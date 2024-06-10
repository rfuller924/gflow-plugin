from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QDialog,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QGroupBox,
)


class ConfigDialog(QDialog):
    """
    Set path to GFLOW executable.
    """

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("Configure GFLOW")
        self.install_task = None

        # Define widgets
        self.browse_button = QPushButton("Browse...")
        self.set_button = QPushButton("Set")
        self.install_zip_line_edit = QLineEdit()
        self.install_zip_line_edit.setMinimumWidth(400)
        self.close_button = QPushButton("Close")

        # Connect with actions
        self.browse_button.clicked.connect(self.set_path)
        self.set_button.clicked.connect(self.set_executable)
        self.close_button.clicked.connect(self.reject)

        # Set layout
        zip_row = QHBoxLayout()
        zip_row.addWidget(QLabel("GFLOW executable"))
        zip_row.addWidget(self.browse_button)
        zip_row.addWidget(self.set_button)

        zip_group = QGroupBox("Set GFLOW executable")
        zip_group.setLayout(zip_row)

        layout = QVBoxLayout()
        layout.addWidget(zip_group)
        layout.addWidget(self.close_button, stretch=0, alignment=Qt.AlignRight)
        layout.addStretch()
        self.setLayout(layout)
 
    def set_path(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select file", "", "*.exe")
        if path != "":  # Empty string in case of cancel button press
            self.install_zip_line_edit.setText(path)
        return

    def set_executable(self) -> None:
        pass