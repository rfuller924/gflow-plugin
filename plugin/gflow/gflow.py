"""Setup a dockwidget to hold the GFLOW plugin widgets."""

from pathlib import Path

from qgis.gui import QgsDockWidget
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction


class GflowPlugin:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.gflow_widget = None
        self.plugin_dir = Path(__file__).parent
        self.pluginIsActive = False
        self.toolbar = iface.addToolBar("GFLOW")
        self.toolbar.setObjectName("GFLOW")
        return

    def add_action(self, icon_name, text="", callback=None, add_to_menu=False):
        icon = QIcon(str(self.plugin_dir / icon_name))
        action = QAction(icon, text, self.iface.mainWindow())
        action.triggered.connect(callback)
        if add_to_menu:
            self.toolbar.addAction(action)
        return action

    def initGui(self):
        icon_name = "icon.png"
        self.action_gflow = self.add_action(icon_name, "GFLOW", self.toggle_gflow, True)

    def toggle_gflow(self):
        if self.gflow_widget is None:
            from .widgets.gflow_widget import GflowWidget

            self.gflow_widget = QgsDockWidget("GFLOW")
            self.gflow_widget.setObjectName("GflowDock")
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.gflow_widget)
            widget = GflowWidget(self.gflow_widget, self.iface)
            self.gflow_widget.setWidget(widget)
            self.gflow_widget.hide()
        self.gflow_widget.setVisible(not self.gflow_widget.isVisible())

    def unload(self):
        self.toolbar.deleteLater()
