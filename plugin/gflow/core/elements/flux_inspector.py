
from qgis.core import QgsSingleSymbolRenderer
from gflow.core.elements.colors import LIGHT_BLUE
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import Required


class FluxInspectorSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
    }


class FluxInspector(Element):
    element_type = "Flux Inspector"
    geometry_type = "Linestring"
    schema = FluxInspectorSchema()

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.line_renderer(color=LIGHT_BLUE, width="0.75", outline_style="dash")

    def process_gflow_row(self, row, other=None):
        return {
            "xy": self.linestring_xy(row),
        }
