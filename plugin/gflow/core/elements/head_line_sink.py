from PyQt5.QtCore import QVariant
from qgis.core import QgsDefaultValue, QgsField, QgsSingleSymbolRenderer
from gflow.core.elements.colors import BLUE
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Positive,
    Required,
    StrictlyPositive,
)


class HeadLineSinkSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "starting_head": Required(),
        "ending_head": Required(),
        "resistance": Required(Positive()),
        "width": Required(StrictlyPositive()),
        "depth": Required(Positive()),
        "label": Required(),
    }


class HeadLineSink(Element):
    element_type = "Head Line Sink"
    geometry_type = "Linestring"
    attributes = (
        QgsField("starting_head", QVariant.Double),
        QgsField("ending_head", QVariant.Double),
        QgsField("resistance", QVariant.Double),
        QgsField("width", QVariant.Double),
        QgsField("depth", QVariant.Double),
        QgsField("label", QVariant.String),
    )
    schema = HeadLineSinkSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.line_renderer(color=BLUE, width="0.75")

    def process_gflow_row(self, row, other=None):
        return {
            "xy": self.linestring_xy(row),
            "starting_head": row["starting_head"],
            "ending_head": row["ending_head"],
            "resistance": row["resistance"],
            "width": row["width"],
            "depth": row["depth"],
            "label": row["label"],
        }
