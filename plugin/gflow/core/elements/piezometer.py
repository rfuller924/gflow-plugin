
from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsSingleSymbolRenderer

from gflow.core.elements.colors import LIGHT_BLUE
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Optional,
    Required,
)


class PiezometerSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "label": Optional(),
    }


class Piezometer(Element):
    element_type = "Piezometer"
    geometry_type = "Point"
    attributes = (
        QgsField("label", QVariant.String),
    )
    schema = PiezometerSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.marker_renderer(color=LIGHT_BLUE, name="triangle", size="3")

    def render(self, row):
        return "{x} {y}".format(**row)
