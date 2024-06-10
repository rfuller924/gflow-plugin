"""
This module contains the classes to represent the GFLOW input layers.

The classes specify:

* The (unabbreviated) name
* The type of geometry (No geometry, point, linestring, polygon)
* The required attributes of the attribute table

They contain logic for setting up:

Each element is (optionally) represented in multiple places:

* It always lives in a GeoPackage.
* While a geopackage is active within plugin, it is always represented in a
  Dataset Tree: the Dataset Tree provides a direct look at the state of the
  GeoPackage.
* It can be added to the Layers Panel in QGIS. This enables a user to visualize
  and edit its data.

Some elements require specific rendering in QGIS (e.g. no fill polygons), which
are supplied by the `.renderer()` staticmethod.

Rendering:

* Fixed discharge (area sink, well, ditch): green
* Fixed head (head well, semi-confined top, head line): blue
* Inhomogeneity: grey
* Constant: star
* Observations: triangle
* Line Doublets: red
* Polygons: Line and Fill same color, Fill color 15% opacity.
"""

import abc
from typing import Any, Dict, List, NamedTuple, Optional, Set, Union

from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)
from qgis.core import (
    QgsFillSymbol,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsSingleSymbolRenderer,
    QgsVectorLayer,
)
from gflow.core import geopackage
from gflow.core.extractor import ExtractorMixin


class ElementExtraction(NamedTuple):
    errors: Optional[Dict[str, Any]] = None
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None


class NameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name_line_edit = QLineEdit()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        first_row = QHBoxLayout()
        first_row.addWidget(QLabel("Layer name"))
        first_row.addWidget(self.name_line_edit)
        second_row = QHBoxLayout()
        second_row.addStretch()
        second_row.addWidget(self.ok_button)
        second_row.addWidget(self.cancel_button)
        layout = QVBoxLayout()
        layout.addLayout(first_row)
        layout.addLayout(second_row)
        self.setLayout(layout)


class Element(ExtractorMixin, abc.ABC):
    """
    Abstract base class for elements.
    """

    element_type = None
    geometry_type = None
    attributes = ()
    attributes = ()
    defaults = {}

    def _initialize_default(self, path, name):
        self.name = name
        self.path = path
        self.gflow_name = None
        self.layer = None
        self.item = None

    def __init__(self, path: str, name: str):
        self._initialize_default(path, name)
        self.gflow_name = f"gflow {self.element_type}:{name}"

    @classmethod
    def dialog(cls, path: str, crs: Any, iface: Any, names: List[str]):
        dialog = NameDialog()
        dialog.show()
        ok = dialog.exec_()
        if not ok:
            return

        name = dialog.name_line_edit.text()
        if name in names:
            raise ValueError(f"Name already exists in geopackage: {name}")

        instance = cls(path, name)
        instance.create_layer(crs)
        return instance

    def _create_layer(
        self, crs: Any, geometry_type: str, name: str, attributes: List
    ) -> QgsVectorLayer:
        layer = QgsVectorLayer(geometry_type, name, "memory")
        provider = layer.dataProvider()
        provider.addAttributes(attributes)
        layer.updateFields()
        layer.setCrs(crs)
        return layer

    def create_layer(self, crs: Any) -> None:
        self.layer = self._create_layer(
            crs=crs,
            geometry_type=self.geometry_type,
            name=self.gflow_name,
            attributes=self.attributes,
        )

    def set_defaults(self) -> None:
        if self.layer is None:
            return
        fields = self.layer.fields()
        for name, definition in self.defaults.items():
            index = fields.indexFromName(name)
            self.layer.setDefaultValueDefinition(index, definition)
        return

    @staticmethod
    def marker_renderer(**kwargs):
        symbol = QgsMarkerSymbol.createSimple(kwargs)
        return QgsSingleSymbolRenderer(symbol)

    @staticmethod
    def line_renderer(**kwargs):
        symbol = QgsLineSymbol.createSimple(kwargs)
        return QgsSingleSymbolRenderer(symbol)

    @staticmethod
    def polygon_renderer(**kwargs):
        symbol = QgsFillSymbol.createSimple(kwargs)
        return QgsSingleSymbolRenderer(symbol)

    @classmethod
    def renderer(cls):
        return None

    def layer_from_geopackage(self) -> QgsVectorLayer:
        self.layer = QgsVectorLayer(
            f"{self.path}|layername={self.gflow_name}", self.gflow_name
        )

    def load_layer_from_geopackage(self) -> None:
        self.layer_from_geopackage()
        self.set_defaults()
        return

    def write(self):
        self.layer = geopackage.write_layer(
            self.path, self.layer, self.gflow_name
        )
        self.set_defaults()

    def remove_from_geopackage(self):
        geopackage.remove_layer(self.path, self.gflow_name)

    @staticmethod
    def _check_table_columns(attributes, layer) -> Dict[str, List]:
        """
        Check if any columns are missing from the table.

        In that case, abort and present an error message.
        """
        fields = set(field.name() for field in layer.fields())
        missing = set(attr.name() for attr in attributes) - fields
        if missing:
            columns = ",".join(missing)
            msg = (
                f"Table is missing columns: {columns}. "
                "Remove and recreate the layer."
            )
            return {"Table:": [msg]}
        return {}

    def check_gflow_columns(self):
        return self._check_table_columns(
            attributes=self.attributes, layer=self.layer
        )

    def to_gflow(self, other=None) -> ElementExtraction:
        missing = self.check_gflow_columns()
        if missing:
            return ElementExtraction(errors=missing)

        data = self.table_to_records(layer=self.layer)
        errors = self.schema.validate_gflow(
            name=self.layer.name(), data=data, other=other
        )

        if errors:
            return ElementExtraction(errors=errors)
        else:
            elements = [self.process_gflow_row(row=row, other=other) for row in data]
            return ElementExtraction(data=elements)

    def extract_data(self, other=None) -> ElementExtraction:
        return self.to_gflow(other)
