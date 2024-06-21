
from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsSingleSymbolRenderer

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
        "label": Optional(),
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

    def render(self, row) -> str:
        NODATA = -9.999e3

        def render_nodata(value):
            if value is None:
                return NODATA
            return value

        conductivity = render_nodata(row["conductivity"])
        base_elevation = render_nodata(row["base_elevation"])
        porosity = render_nodata(row["porosity"])
        average_head = render_nodata(row["average_head"])

        # Flip sign on recharge
        recharge = row["recharge"]
        if recharge is None:
            recharge = NODATA
        else:
            recharge *= -1.0

        return (
            f"transmissivity {conductivity} {base_elevation} {average_head} {recharge} {porosity}\n"
            + self._render_xy(row["xy"])
        )
