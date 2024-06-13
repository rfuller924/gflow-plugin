import textwrap

import numpy as np
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

    def render(self, row) -> str:
        parameters = textwrap.dedent("""\
            head
            resistance {resistance}
            width {width}
            depth {depth}"""
        ).format(**row)

        starting_head = row["starting_head"]
        ending_head = row["ending_head"]
        xy = np.array(row["xy"])
        distance = np.linalg.norm(np.diff(xy, axis=1), axis=1)
        accumulated = distance.cumsum()
        # Compute midpoint along segmenets
        midpoint = accumulated - 0.5 * distance
        # Linearly interpolate head to midpoint of segment
        midpoint_head = starting_head + (midpoint / accumulated[-1]) * (ending_head - starting_head)

        lines = [parameters]
        for head, (x0, y0), (x1, y1) in zip(midpoint_head, xy[:-1], xy[1:]):
            lines.append(f"{x0} {y0} {x1} {y1} {head}")

        return "\n".join(lines)
