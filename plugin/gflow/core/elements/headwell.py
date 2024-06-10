from typing import Any, Dict

from PyQt5.QtCore import QVariant
from qgis.core import  QgsField, QgsSingleSymbolRenderer
from gflow.core.elements.colors import BLUE
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Required,
    StrictlyPositive,
)


class WellSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "head": Required(),
        "radius": Required(StrictlyPositive()),
        "label": Required(),
    }


class HeadWell(Element):
    element_type = "Head Well"
    geometry_type = "Point"
    attributes = (
        QgsField("head", QVariant.Double),
        QgsField("radius", QVariant.Double),
        QgsField("label", QVariant.String),
    )
    schema = WellSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.marker_renderer(color=BLUE, size="3")

    def process_gflow_row(self, row, other=None) -> Dict[str, Any]:
        x, y = self.point_xy(row)
        return {
            "x": x,
            "y": y,
            "head": row["discharge"],
            "radius": row["radius"],
            "label": row["label"],
        }
