
from PyQt5.QtCore import QVariant
from qgis.core import QgsDefaultValue, QgsField, QgsSingleSymbolRenderer
from gflow.core.elements.colors import RED
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import Required, StrictlyPositive


class BarrierSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "conductivity": Required(StrictlyPositive()),
        "thickness": Required(StrictlyPositive()),
        "porosity": Required(StrictlyPositive()),
        "bottom_elevation": Required(),
        "label": Required(),
    }


class Barrier(Element):
    element_type = "Barrier"
    geometry_type = "Linestring"
    attributes = (
        QgsField("conductivity", QVariant.Double),
        QgsField("thickness", QVariant.Double),
        QgsField("porosity", QVariant.Double),
        QgsField("bottom_elevation", QVariant.Double),
        QgsField("label", QVariant.String),
    )
    schema = BarrierSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.line_renderer(color=RED, width="0.75", outline_style="dash")

    def process_gflow_row(self, row, other=None):
        return {
            "xy": self.linestring_xy(row),
            "conductivity": row["conductivity"],
            "thickness": row["thickness"],
            "porosity": row["porosity"],
            "bottom_elevation": row["bottom_elevation"],
            "label": row["label"],
        }
