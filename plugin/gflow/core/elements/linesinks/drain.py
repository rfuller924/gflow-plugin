import textwrap

from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsSingleSymbolRenderer

from gflow.core.elements.colors import LIGHT_BLUE
from gflow.core.elements.element import LineSink
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Membership,
    Optional,
    Positive,
    Required,
    StrictlyPositive,
)


class DrainLineSinkSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "starting_head": Required(),
        "ending_head": Required(),
        "resistance": Required(Positive()),
        "width": Required(StrictlyPositive()),
        "location": Required(Membership(LineSink.LINESINKLOCATIONS.keys())),
        "label": Optional(),
    }


class DrainLineSink(LineSink):
    element_type = "Drain Line Sink"
    geometry_type = "Linestring"
    attributes = (
        QgsField("starting_head", QVariant.Double),
        QgsField("ending_head", QVariant.Double),
        QgsField("resistance", QVariant.Double),
        QgsField("width", QVariant.Double),
        QgsField("location", QVariant.String),
        QgsField("label", QVariant.String),
    )
    schema = DrainLineSinkSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.line_renderer(color=LIGHT_BLUE, width="0.75")

    def render(self, row) -> str:
        self._set_location(row)
        parameters = textwrap.dedent("""\
            drain
            resistance {resistance}
            width {width} {location}
            depth 0.0""").format(**row)

        lines = [parameters] + self._interpolate_along_segments(
            xy=row["xy"],
            start=row["starting_head"],
            end=row["ending_head"],
        )
        return "\n".join(lines)
