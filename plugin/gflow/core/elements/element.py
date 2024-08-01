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
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Union

import numpy as np
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)
from qgis.core import (
    QgsDefaultValue,
    QgsEditorWidgetSetup,
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
    rendered: Optional[str] = None


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
    """Abstract base class for elements."""

    element_type: str
    geometry_type: str
    attributes: tuple = ()
    defaults: dict = {}

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

    def set_dropdown(self, name: str, options: Sequence[str]) -> None:
        """Use a dropdown menu for a field in the editor widget."""
        layer = self.layer
        index = layer.fields().indexFromName(name)
        setup = QgsEditorWidgetSetup(
            "ValueMap",
            {"map": {value: value for value in options}},
        )
        layer.setEditorWidgetSetup(index, setup)
        return

    def set_editor_widget(self) -> None:
        pass

    def layer_from_geopackage(self) -> QgsVectorLayer:
        self.layer = QgsVectorLayer(
            f"{self.path}|layername={self.gflow_name}", self.gflow_name
        )

    def load_layer_from_geopackage(self) -> None:
        self.layer_from_geopackage()
        self.set_defaults()
        self.set_editor_widget()
        return

    def write(self):
        self.layer = geopackage.write_layer(self.path, self.layer, self.gflow_name)
        self.set_defaults()
        self.set_editor_widget()
        return

    def remove_from_geopackage(self):
        geopackage.remove_layer(self.path, self.gflow_name)

    def check_table_columns(self) -> Dict[str, List]:
        """
        Check if any columns are missing from the table.

        In that case, abort and present an error message.
        """
        layer = self.layer
        attributes = self.attributes
        fields = {field.name() for field in layer.fields()}
        missing = {attr.name() for attr in attributes} - fields
        if missing:
            columns = ",".join(missing)
            msg = (
                f"Table is missing columns: {columns}. "
                "Remove and recreate the layer."
            )
            return {"Table:": [msg]}
        return {}

    def process_table_row(self, row) -> tuple[Dict[str, Any], str]:
        gflow_row = row.copy()
        gflow_row.pop("geometry", None)
        gflow_row.pop("fid", None)

        match self.geometry_type:
            case "No Geometry":
                pass
            case "Point":
                gflow_row["x"], gflow_row["y"] = self.point_xy(row)
            case "Linestring":
                gflow_row["xy"] = self.linestring_xy(row)
            case "Polygon":
                gflow_row["xy"] = self.polygon_xy(row)

        rendered = self.render(gflow_row)
        return gflow_row, rendered

    def extract_data(self) -> ElementExtraction:
        missing = self.check_table_columns()
        if missing:
            return ElementExtraction(errors=missing)

        data = self.table_to_records(layer=self.layer)
        errors = self.schema.validate(name=self.layer.name(), data=data)

        if errors:
            return ElementExtraction(errors=errors)
        else:
            elements = []
            rendered = []
            for row in data:
                data, string = self.process_table_row(row)
                elements.append(data)
                rendered.append(string)
            return ElementExtraction(data=data, rendered=rendered)

    def _render_xy(self, xy) -> str:
        return "\n".join(f"{x} {y}" for (x, y) in xy)


class LineSink(Element, abc.ABC):
    element_type = "Head Line Sink"
    geometry_type = "Linestring"
    LINESINKLOCATIONS = {
        "Unknown": 0,
        "Along stream centerline": 1,
        "Along surface water boundary": 2,
    }
    defaults = {
        "location": QgsDefaultValue("Unknown"),
    }

    def set_editor_widget(self) -> None:
        self.set_dropdown("location", self.LINESINKLOCATIONS.keys())

    def _set_location(self, row) -> None:
        row["location"] = self.LINESINKLOCATIONS[row["location"]]

    @staticmethod
    def _interpolate_along_segments(xy, start, end) -> list[str]:
        xy = np.array(xy)
        distance = np.linalg.norm(np.diff(xy, axis=1), axis=1)
        accumulated = distance.cumsum()
        # Compute midpoint along segmenets
        midpoint = accumulated - 0.5 * distance
        # Linearly interpolate head to midpoint of segment
        midpoint_values = start + (midpoint / accumulated[-1]) * (end - start)

        lines = []
        for value, (x0, y0), (x1, y1) in zip(midpoint_values, xy[:-1], xy[1:]):
            lines.append(f"{x0} {y0} {x1} {y1} {value}")
        return lines
