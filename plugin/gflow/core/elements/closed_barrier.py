from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsSingleSymbolRenderer

from gflow.core.elements.colors import RED, TRANSPARENT_RED
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Optional,
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
        "label": Optional(),
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

    def render(self, row) -> str:
        return (
            "slurry closed {conductivity} {thickness} {porosity} {bottom_elevation}\n".format(
                **row
            )
            + self._render_xy(row["xy"])
        )
