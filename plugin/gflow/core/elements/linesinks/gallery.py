import textwrap

from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsSingleSymbolRenderer

from gflow.core.elements.colors import GREEN
from gflow.core.elements.element import LineSink
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Membership,
    Optional,
    Positive,
    Required,
    StrictlyPositive,
)


class GalleryLineSinkSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "discharge": Required(),
        "minimum_starting_head": Required(),
        "minimum_ending_head": Required(),
        "resistance": Required(Positive()),
        "width": Required(StrictlyPositive()),
        "depth": Required(Positive()),
        "location": Required(Membership(LineSink.LINESINKLOCATIONS.keys())),
        "label": Optional(),
    }


class GalleryLineSink(LineSink):
    element_type = "Gallery Line Sink"
    geometry_type = "Linestring"
    attributes = (
        QgsField("discharge", QVariant.Double),
        QgsField("minimum_starting_head", QVariant.Double),
        QgsField("minimum_ending_head", QVariant.Double),
        QgsField("resistance", QVariant.Double),
        QgsField("width", QVariant.Double),
        QgsField("depth", QVariant.Double),
        QgsField("location", QVariant.String),
        QgsField("label", QVariant.String),
    )
    schema = GalleryLineSinkSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.line_renderer(color=GREEN, width="0.75")

    def render(self, row) -> str:
        self._set_location(row)
        parameters = textwrap.dedent("""\
            gallery
            pumping {discharge}
            resistance {resistance}
            width {width} {location}
            depth 0.0""").format(**row)

        lines = [parameters] + self._interpolate_along_segments(
            xy=row["xy"],
            start=row["minimum_starting_head"],
            end=row["minimum_ending_head"],
        )
        return "\n".join(lines)
