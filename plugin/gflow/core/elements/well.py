
from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsSingleSymbolRenderer

from gflow.core.elements.colors import GREEN
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Optional,
    Required,
    StrictlyPositive,
)


class WellSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "discharge": Required(),
        "radius": Required(StrictlyPositive()),
        "label": Optional(),
    }


class Well(Element):
    element_type = "Well"
    geometry_type = "Point"
    attributes = (
        QgsField("discharge", QVariant.Double),
        QgsField("radius", QVariant.Double),
        QgsField("label", QVariant.String),
    )
    schema = WellSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.marker_renderer(color=GREEN, size="3")

    def render(self, row):
        return "{x} {y} {discharge} {radius}".format(**row)
