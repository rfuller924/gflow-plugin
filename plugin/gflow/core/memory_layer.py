import abc
from qgis.core import (
    edit,
    QgsVectorLayer,
    QgsFeature,
    QgsPointXY,
    QgsGeometry,
)


class MemoryLayer(abc.ABC):
    def __init__(self, name, crs, attributes):
        layer = QgsVectorLayer(self.geometry_type, name, "memory")
        provider = layer.dataProvider()
        provider.addAttributes(attributes)
        layer.updateFields()
        layer.setCrs(crs)
        self.layer = layer

    @classmethod
    @abc.abstractmethod
    def _create_geometry(cls, x, y):
        pass

    def add_features_from_records(self, records) -> None:
        fields = self.layer.fields()
        fieldnames = [f.name() for f in fields]
        features = []
        for record in records:
            geometry = self._create_geometry(record["x"], record["y"])
            feature = QgsFeature(fields)
            feature.setGeometry(geometry)
            feature.setAttributes([record.get(f) for f in fieldnames])
            features.append(feature)

        with edit(self.layer):
            self.layer.addFeatures(features)

        return


class PointMemoryLayer(MemoryLayer):
    geometry_type = "Point"

    def _create_geometry(self, x, y):
        return QgsGeometry.fromPointXY(QgsPointXY(x, y))


class LinestringMemoryLayer(MemoryLayer):
    geometry_type = "Linestring"

    def _create_geometry(self, x, y):
        vertices = [QgsPointXY(px, py) for (px, py) in zip(x, y)]
        return QgsGeometry.fromPolylineXY(vertices)


class PolygonMemoryLayer(MemoryLayer):
    geometry_type = "Polygon"

    def _create_geometry(self, x, y):
        vertices = [QgsPointXY(px, py) for (px, py) in zip(x, y)]
        polygon = [vertices]  # Nota bene: list of lists for holes, etc.!
        return QgsGeometry.fromPolygonXY(polygon)
