from typing import Any, Dict

from PyQt5.QtCore import QVariant
from qgis.core import QgsDefaultValue, QgsField, QgsSingleSymbolRenderer
from gflow.core.elements.colors import GREY, TRANSPARENT_GREY
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Optional,
    Required,
    StrictlyPositive,
)


class InhomogeneitySchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "conductivity": Optional(StrictlyPositive()),
        "recharge": Optional(),
        "porosity": Optional(StrictlyPositive()),
        "base_elevation": Optional(),
        "average_head": Optional(),
        "label": Required(),
    }


class Inhomogeneity(Element):
    element_type = "Inhomogeneity"
    geometry_type = "Polygon"
    attributes = (
        QgsField("conductivity", QVariant.Double),
        QgsField("recharge", QVariant.Double),
        QgsField("porosity", QVariant.Double),
        QgsField("base_elevation", QVariant.Double),
        QgsField("average_head", QVariant.Double),
        QgsField("label", QVariant.String),
    )
    schema = InhomogeneitySchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.polygon_renderer(
            color=TRANSPARENT_GREY, color_border=GREY, width_border="0.75"
        )

    def process_gflow_row(self, row: Dict[str, Any], grouped: Dict[int, Any]):
        return {
            "xy": self.polygon_xy(row),
            "order": row["order"],
            "ndeg": row["ndegrees"],
        }
