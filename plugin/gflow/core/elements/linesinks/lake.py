import textwrap

from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsSingleSymbolRenderer

from gflow.core.elements.colors import BLUE
from gflow.core.elements.element import LineSink
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Membership,
    Optional,
    Positive,
    Required,
    StrictlyPositive,
)


class LakeLineSinkSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "lake_bottom": Required(),
        "estimted_level1": Required(),
        "estimted_level2": Required(),
        "resistance": Required(Positive()),
        "width": Required(StrictlyPositive()),
        "depth": Required(Positive()),
        "location": Required(Membership(LineSink.LINESINKLOCATIONS.keys())),
        "label": Optional(),
    }


class LakeLineSink(LineSink):
    element_type = "Lake Line Sink"
    geometry_type = "Linestring"
    attributes = (
        QgsField("lake_bottom", QVariant.Double),
        QgsField("estimated_level1", QVariant.Double),
        QgsField("estimated_level2", QVariant.Double),
        QgsField("width", QVariant.Double),
        QgsField("depth", QVariant.Double),
        QgsField("location", QVariant.String),
        QgsField("label", QVariant.String),
    )
    schema = LakeLineSinkSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.line_renderer(color=BLUE, width="0.75")

    def render(self, row) -> str:
        self._set_location(row)
        parameters = textwrap.dedent("""\
            head
            resistance {resistance}
            width {width} {location}
            depth {depth}""").format(**row)

        lines = [parameters] + self._interpolate_along_segments(
            xy=row["xy"],
            start=row["starting_head"],
            end=row["ending_head"],
        )
        return "\n".join(lines)
