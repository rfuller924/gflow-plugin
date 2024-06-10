from typing import Any, Tuple

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsSingleSymbolRenderer,
)
from gflow.core.elements.colors import BLACK
from gflow.core.elements.element import ElementExtraction, Element
from gflow.core.elements.schemata import SingleRowSchema
from gflow.core.schemata import Required, Required


class DomainSchema(SingleRowSchema):
    schemata = {"geometry": Required()}

class Domain(Element):
    element_type = "Domain"
    geometry_type = "Polygon"
    gflow_attributes = (QgsField("time", QVariant.Double),)
    schema = DomainSchema()

    def __init__(self, path: str, name: str):
        self._initialize_default(path, name)
        self.gflow_name = f"gflow {self.element_type}:Domain"

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        """
        Results in transparent fill, with a medium thick black border line.
        """
        return cls.polygon_renderer(
            color="255,0,0,0", color_border=BLACK, width_border="0.75"
        )

    def remove_from_geopackage(self):
        pass

    def update_extent(self, iface: Any) -> Tuple[float, float]:
        provider = self.layer.dataProvider()
        provider.truncate()  # removes all features
        canvas = iface.mapCanvas()
        extent = canvas.extent()
        xmin = extent.xMinimum()
        ymin = extent.yMinimum()
        xmax = extent.xMaximum()
        ymax = extent.yMaximum()
        points = [
            QgsPointXY(xmin, ymax),
            QgsPointXY(xmax, ymax),
            QgsPointXY(xmax, ymin),
            QgsPointXY(xmin, ymin),
        ]
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPolygonXY([points]))
        provider.addFeatures([feature])
        canvas.refresh()
        return ymax, ymin

    def to_gflow(self, other) -> ElementExtraction:
        data = self.table_to_records(layer=self.layer)
        errors = self.schema.validate_gflow(
            name=self.layer.name(), data=data, other=other
        )
        if errors:
            return ElementExtraction(errors=errors)
        else:
            x = [point[0] for point in data[0]["geometry"]]
            y = [point[1] for point in data[0]["geometry"]]
            return ElementExtraction(
                data={
                    "xmin": min(x),
                    "xmax": max(x),
                    "ymin": min(y),
                    "ymax": max(y),
                }
            )
