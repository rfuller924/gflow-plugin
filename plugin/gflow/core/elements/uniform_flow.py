from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsSingleSymbolRenderer
from gflow.core.elements.colors import RED
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import SingleRowSchema
from gflow.core.schemata import Required


class UniformFlowSchema(SingleRowSchema):
    schemata = {
        "geometry": Required(),
        "head": Required(),
        "gradient": Required(),
        "orientation": Required(),
        "label": Required(),
    }


class UniformFlow(Element):
    element_type = "Uniform Flow"
    geometry_type = "Point"
    attributes = (
        QgsField("head", QVariant.Double),
        QgsField("gradient", QVariant.Double),
        QgsField("orientation", QVariant.Double),
    )
    schema = UniformFlowSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.marker_renderer(color=RED, name="star", size="5")

    def process_gflow_row(self, row, other=None):
        return {
            "head": row["head"],
            "gradient": row["gradient"],
            "orientation": row["orientation"],
        }
