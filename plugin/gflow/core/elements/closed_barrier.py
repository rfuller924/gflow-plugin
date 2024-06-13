from typing import Any, Dict

from PyQt5.QtCore import QVariant
from qgis.core import QgsDefaultValue, QgsField, QgsSingleSymbolRenderer
from gflow.core.elements.colors import RED, TRANSPARENT_RED
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Required,
    StrictlyPositive,
)


class ClosedBarrierSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "conductivity": Required(StrictlyPositive()),
        "thickness": Required(StrictlyPositive()),
        "porosity": Required(StrictlyPositive()),
        "bottom_elevation": Required(),
        "label": Required(),
    }


class ClosedBarrier(Element):
    element_type = "Closed Barrier"
    geometry_type = "Polygon"
    attributes = (
        QgsField("conductivity", QVariant.Double),
        QgsField("thickness", QVariant.Double),
        QgsField("porosity", QVariant.Double),
        QgsField("bottom_elevation", QVariant.Double),
        QgsField("label", QVariant.String),
        QgsField("ignore_inside", QVariant.Bool),
        QgsField("ignore_outside", QVariant.Bool),
    )
    schema = ClosedBarrierSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.polygon_renderer(
            color=TRANSPARENT_RED,
            color_border=RED,
            width_border="0.75",
            outline_style="dash",
        )
