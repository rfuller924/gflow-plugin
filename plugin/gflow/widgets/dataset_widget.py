"""
This widgets displays the available elements in the GeoPackage.

This widget also allows enabling or disabling individual elements for a
computation.
"""

import json
from collections import defaultdict
from pathlib import Path
from shutil import copy
from typing import Any, Dict, List, NamedTuple, Set, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qgis.core import Qgis, QgsProject, QgsUnitTypes

from gflow.core.elements import Aquifer, Domain, load_elements_from_geopackage
from gflow.core.formatting import data_to_gflow
from gflow.widgets.error_window import ValidationDialog


class Extraction(NamedTuple):
    gflow: Dict[str, Any] = None
    success: bool = True


class DatasetTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setHeaderHidden(True)
        self.setSortingEnabled(True)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.setHeaderLabels(["   ", "element"])
        self.setHeaderHidden(False)
        self.setColumnCount(2)
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionsMovable(False)
        self.domain = None

    def items(self) -> List[QTreeWidgetItem]:
        root = self.invisibleRootItem()
        return [root.child(i) for i in range(root.childCount())]

    def reset(self):
        for item in self.items():
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)
        return

    def add_item(self, gflow_name: str, enabled: bool = True):
        item = QTreeWidgetItem()
        self.addTopLevelItem(item)
        item.gflow_checkbox = QCheckBox()
        item.gflow_checkbox.setChecked(True)
        item.gflow_checkbox.setEnabled(enabled)
        self.setItemWidget(item, 0, item.gflow_checkbox)
        item.setText(1, gflow_name)
        return item

    def add_element(self, element) -> None:
        # These are mandatory elements, cannot be unticked
        if isinstance(element, (Domain, Aquifer)):
            enabled = False
        else:
            enabled = True

        item = self.add_item(gflow_name=element.gflow_name, enabled=enabled)
        item.element = element
        return

    def remove_geopackage_layers(self) -> None:
        """
        Remove layers from:

        * The dataset tree widget
        * The QGIS layer panel
        * The geopackage
        """
        # Collect the selected items
        selection = self.selectedItems()
        selection = [
            item
            for item in selection
            if not isinstance(item.element, (Aquifer, Domain))
        ]

        # Warn before deletion
        message = "\n".join([f"- {item.text(1)}" for item in selection])
        reply = QMessageBox.question(
            self,
            "Deleting from Geopackage",
            f"Deleting:\n{message}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        # Start deleting
        elements = {item.element for item in selection}
        qgs_instance = QgsProject.instance()

        for element in elements:
            layer = element.layer
            # QGIS layers
            if layer is None:
                continue
            try:
                qgs_instance.removeMapLayer(layer.id())
            except (RuntimeError, AttributeError) as e:
                if e.args[0] in (
                    "wrapped C/C++ object of type QgsVectorLayer has been deleted",
                    "'NoneType' object has no attribute 'id'",
                ):
                    pass
                else:
                    raise

            # Geopackage
            element.remove_from_geopackage()

        for item in selection:
            # Dataset tree
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)

        return

    def extract_data(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract the data of the Geopackage.

        Validates all data while converting, and returns a list of validation
        errors if something is amiss.
        """
        data = defaultdict(dict)
        errors = {}
        elements = {
            item.text(1): item.element
            for item in self.items()
            if item.gflow_checkbox.isChecked()
        }

        for name, element in elements.items():
            try:
                extraction = element.extract_data()
                if extraction.errors:
                    errors[name] = extraction.errors
                elif extraction.data:  # skip empty tables
                    data[element.element_type][name] = extraction
            except RuntimeError as e:
                if (
                    e.args[0]
                    == "wrapped C/C++ object of type QgsVectorLayer has been deleted"
                ):
                    # Delay of Qt garbage collection to blame?
                    pass
                else:
                    raise e

        return errors, data


class DatasetWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.dataset_tree = DatasetTreeWidget()
        self.model_crs = None
        self.start_task = None
        self.dataset_tree.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.dataset_line_edit = QLineEdit()
        self.dataset_line_edit.setEnabled(False)  # Just used as a viewing port
        self.open_geopackage_button = QPushButton("Open")
        self.new_geopackage_button = QPushButton("New")
        self.save_geopackage_button = QPushButton("Save as")
        self.restore_geopackage_button = QPushButton("Restore")
        self.remove_button = QPushButton("Remove from Model")
        self.add_button = QPushButton("Add to QGIS")
        self.open_geopackage_button.clicked.connect(self.open_geopackage)
        self.new_geopackage_button.clicked.connect(self.new_geopackage)
        self.save_geopackage_button.clicked.connect(self.save_geopackage)
        self.restore_geopackage_button.clicked.connect(self.restore_geopackage)
        self.suppress_popup_checkbox = QCheckBox(
            "Suppress attribute form pop-up after feature creation"
        )
        self.suppress_popup_checkbox.stateChanged.connect(self.suppress_popup_changed)
        self.remove_button.clicked.connect(self.remove_geopackage_layer)
        self.add_button.clicked.connect(self.add_selection_to_qgis)
        self.gflow_convert_button = QPushButton("Save as GFLOW .dat")
        self.gflow_convert_button.clicked.connect(self.save_as_gflow)
        self.json_convert_button = QPushButton("Save as JSON")
        self.json_convert_button.clicked.connect(self.save_as_json)
        self.reset()
        # Layout
        dataset_layout = QVBoxLayout()

        # Add geopackage management
        geopackage_group = QGroupBox("GeoPackage")
        geopackage_layout = QVBoxLayout()
        geopackage_group.setLayout(geopackage_layout)
        geopackage_layout.addWidget(self.dataset_line_edit)
        geopackage_row = QHBoxLayout()
        geopackage_row.addWidget(self.new_geopackage_button)
        geopackage_row.addWidget(self.open_geopackage_button)
        geopackage_row.addWidget(self.save_geopackage_button)
        geopackage_row.addWidget(self.restore_geopackage_button)
        geopackage_layout.addLayout(geopackage_row)
        convert_row = QHBoxLayout()
        convert_row.addWidget(self.gflow_convert_button)
        convert_row.addWidget(self.json_convert_button)
        geopackage_layout.addLayout(convert_row)
        dataset_layout.addWidget(geopackage_group)

        model_setup_group = QGroupBox("Model Setup")
        model_setup_layout = QVBoxLayout()
        model_setup_group.setLayout(model_setup_layout)
        mode_row = QHBoxLayout()
        model_setup_layout.addLayout(mode_row)
        # Dataset table and suppression checkbox
        model_setup_layout.addWidget(self.dataset_tree)
        # Assorted widgets
        model_setup_layout.addWidget(self.suppress_popup_checkbox)
        layer_row = QHBoxLayout()
        layer_row.addWidget(self.add_button)
        layer_row.addWidget(self.remove_button)
        model_setup_layout.addLayout(layer_row)
        dataset_layout.addWidget(model_setup_group)
        self.setLayout(dataset_layout)
        self.validation_dialog = None

    @property
    def path(self) -> str:
        """Returns currently active path to GeoPackage."""
        return self.dataset_line_edit.text()

    def reset(self):
        # Set state back to defaults
        self.save_geopackage_button.setEnabled(False)
        self.json_convert_button.setEnabled(False)
        self.gflow_convert_button.setEnabled(False)
        self.start_task = None
        self.dataset_line_edit.setText("")
        self.dataset_tree.reset()
        return

    def add_item_to_qgis(self, item) -> None:
        # Get all the relevant data.
        element = item.element
        element.load_layer_from_geopackage()
        suppress = self.suppress_popup_checkbox.isChecked()
        # Start adding the layers
        maplayer = self.parent.input_group.add_layer(
            element.layer, "gflow", element.renderer(), suppress
        )
        # Set cell size if the item is a domain layer
        if item.element.gflow_name.split(":")[0] == "gflow Domain":
            if maplayer.featureCount() <= 0:
                return
            feature = next(iter(maplayer.getFeatures()))
            extent = feature.geometry().boundingBox()
            ymax = extent.yMaximum()
            ymin = extent.yMinimum()
            self.parent.set_spacing_from_domain(ymax, ymin)
        return

    def add_selection_to_qgis(self) -> None:
        selection = self.dataset_tree.selectedItems()
        for item in selection:
            self.add_item_to_qgis(item)
        return

    def load_geopackage(self, input_group: str = None) -> None:
        """Load the layers of a GeoPackage into the Layers Panel."""
        self.dataset_tree.clear()

        if input_group is None:
            name = str(Path(self.path).stem)
            input_group = f"{name} input"
        self.parent.create_input_group(input_group)

        elements = load_elements_from_geopackage(self.path)
        for element in elements:
            self.dataset_tree.add_element(element)

        for item in self.dataset_tree.items():
            self.add_item_to_qgis(item)

        self.dataset_tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.parent.enable_geopackage_buttons()
        self.model_crs = self.domain_item().element.layer.crs()
        self.parent.qgs_project.writeEntry("gflow", "geopackage_path", self.path)
        self.parent.qgs_project.writeEntry("gflow", "input_group", input_group)
        return

    def new_geopackage(self) -> None:
        """
        Create a new GeoPackage file, and set it as the active dataset.

        The CRS is important since GFLOW always assumes a Cartesian reference
        plane, and variables such as conductivity are expressed in units such
        as meter per day. As distances are inferred from the geometry, the
        geometry must have appropriate units.
        """
        crs = self.parent.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.mapUnits() not in (
            QgsUnitTypes.DistanceMeters,
            QgsUnitTypes.DistanceFeet,
        ):
            msg = "Project Coordinate Reference System map units are not meters or feet"
            self.parent.message_bar.pushMessage("Error", msg, level=Qgis.Critical)
            return

        path, _ = QFileDialog.getSaveFileName(self, "Select file", "", "*.gpkg")
        if path != "":  # Empty string in case of cancel button press
            self.dataset_line_edit.setText(path)
            # Writing here creates a new Geopackage.
            for element in (Aquifer, Domain):
                instance = element(self.path, "")
                instance.create_layer(crs)
                instance.write()
            # Next, we load the newly written layers.
            self.load_geopackage()

        return

    def open_geopackage(self) -> None:
        """Open a GeoPackage file, containing qgis-tim."""
        path, _ = QFileDialog.getOpenFileName(self, "Select file", "", "*.gpkg")
        if path != "":  # Empty string in case of cancel button press
            self.dataset_line_edit.setText(path)
            try:
                self.load_geopackage()
            except:  # noqa: E722
                msg = f"GeoPackage is not valid QGIS-Tim model input: {path}"
                self.parent.message_bar.pushMessage("Error", msg, level=Qgis.Critical)
                self.dataset_line_edit.setText("")
        return

    def save_geopackage(self) -> None:
        """Copy a GeoPackage file containing qgis-tim."""
        # Do nothing if there's nothing to copy.
        if self.path == "":
            return
        target_path, _ = QFileDialog.getSaveFileName(self, "Select file", "", "*.gpkg")
        if target_path != "":  # Empty string in case of cancel button press
            source_path = Path(self.path)
            target_path = Path(target_path)
            copy(source_path, target_path)
            # Take into account the wal (write-ahead-logging) and shm files as well:
            for suffix in (".gpkg-wal", ".gpkg-shm"):
                extra_source = source_path.with_suffix(suffix)
                extra_target = target_path.with_suffix(suffix)
                if extra_source.exists():
                    copy(extra_source, extra_target)
        return

    def restore_geopackage(self) -> None:
        qgs_project = self.parent.qgs_project
        geopackage_path, success = qgs_project.readEntry("gflow", "geopackage_path")
        if not success:
            self.parent.message_bar.pushMessage(
                title="Error",
                text="Could not find a QGIS-Tim GeoPackage in this QGIS Project.",
                level=Qgis.Critical,
            )
            return

        if not Path(geopackage_path).exists():
            self.parent.message_bar.pushMessage(
                title="Error",
                text=f"QGIS-Tim Geopackage {geopackage_path} does not exist.",
                level=Qgis.Critical,
            )

        input_group_name, _ = qgs_project.readEntry("gflow", "input_group")

        reply = QMessageBox.question(
            self,
            "Restore Model from Project",
            f"Re-create Layers Panel group: {input_group_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        self.dataset_line_edit.setText(geopackage_path)
        self.load_geopackage(input_group_name)
        return

    def remove_geopackage_layer(self) -> None:
        """
        Remove layers from:
        * The dataset tree widget
        * The QGIS layer panel
        * The geopackage.
        """
        self.dataset_tree.remove_geopackage_layers()
        return

    def suppress_popup_changed(self):
        suppress = self.suppress_popup_checkbox.isChecked()
        for item in self.dataset_tree.items():
            layer = item.element.layer
            if layer is not None:
                config = layer.editFormConfig()
                config.setSuppress(suppress)
                layer.setEditFormConfig(config)
        return

    def active_elements(self):
        active_elements = {}
        for item in self.dataset_tree.items():
            active_elements[item.text(1)] = not (item.gflow_checkbox.isChecked() == 0)
        return active_elements

    def domain_item(self):
        for item in self.dataset_tree.items():
            if isinstance(item.element, Domain):
                return item
        else:
            # Create domain instead?
            raise ValueError("Geopackage does not contain domain")

    def selection_names(self) -> Set[str]:
        selection = self.dataset_tree.items()
        return {item.element.name for item in selection}

    def add_element(self, element) -> None:
        self.dataset_tree.add_element(element)
        return

    def set_interpreter_interaction(self, value: bool):
        self.parent.set_interpreter_interaction(value)
        return

    def _extract_data(self) -> Extraction:
        if self.validation_dialog:
            self.validation_dialog.close()
            self.validation_dialog = None

        errors, gflow_data = self.dataset_tree.extract_data()
        if errors:
            self.validation_dialog = ValidationDialog(errors)
            return Extraction(success=False)

        return Extraction(gflow=gflow_data)

    def convert_to_gflow(self, path: str) -> bool:
        extraction = self._extract_data()
        if not extraction.success:
            return

        dat_content = data_to_gflow(
            extraction.gflow,
            name=str(Path(self.path).stem),
            output_options=self.parent.compute_widget.output_options,
        )

        with open(path, "w") as f:
            f.write(dat_content)

        self.parent.message_bar.pushMessage(
            title="Info",
            text=f"Converted geopackage to GFLOW .dat file: {path}",
            level=Qgis.Info,
        )
        return False

    def save_as_gflow(self) -> bool:
        outpath, _ = QFileDialog.getSaveFileName(self, "Select file", "", "*.dat")
        if outpath == "":  # Empty string in case of cancel button press
            return
        self.convert_to_gflow(outpath)
        return

    def convert_to_json(
        self,
        path: str,
    ) -> bool:
        """
        Parameters
        ----------
        path: str
            Path to JSON file to write.

        Returns
        -------
        invalid_input: bool
            Whether validation has succeeded.

        """
        extraction = self._extract_data()
        if not extraction.success:
            return True

        json_data = data_to_json(
            extraction.gflow,
            output_options=self.parent.compute_widget.output_options,
        )

        crs = self.parent.crs
        organization, srs_id = crs.authid().split(":")
        json_data["crs"] = {
            "description": crs.description(),
            "organization": organization,
            "srs_id": srs_id,
            "wkt": crs.toWkt(),
        }

        with open(path, "w") as fp:
            json.dump(json_data, fp=fp, indent=4)

        self.parent.message_bar.pushMessage(
            title="Info",
            text=f"Converted geopackage to JSON: {path}",
            level=Qgis.Info,
        )
        return False

    def save_as_json(self) -> None:
        outpath, _ = QFileDialog.getSaveFileName(self, "Select file", "", "*.json")
        if outpath == "":  # Empty string in case of cancel button press
            return

        self.convert_to_json(outpath)
        return
