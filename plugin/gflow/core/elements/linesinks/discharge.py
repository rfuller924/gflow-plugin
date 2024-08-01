from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsSingleSymbolRenderer

from gflow.core.elements.colors import GREEN
from gflow.core.elements.element import LineSink
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Membership,
    Optional,
    Required,
)


class DischargeLineSinkSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "starting_density": Required(),
        "ending_density": Required(),
        "label": Optional(),
    }


class DischargeLineSink(LineSink):
    element_type = "Discharge Line Sink"
    geometry_type = "Linestring"
    attributes = (
        QgsField("starting_density", QVariant.Double),
        QgsField("ending_density", QVariant.Double),
        QgsField("label", QVariant.String),
    )
    schema = DischargeLineSinkSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.line_renderer(color=GREEN, width="0.75")

    def render(self, row) -> str:
        lines = ["discharge"] + self._interpolate_along_segments(
            xy=row["xy"],
            start=row["starting_density"],
            end=row["ending_density"],
        )
        return "\n".join(lines)
