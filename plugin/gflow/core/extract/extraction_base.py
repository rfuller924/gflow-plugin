import abc
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QVariant

from qgis.core import QgsVectorLayer, QgsField

from gflow.core import geopackage


class Extraction(abc.ABC):
    def __init__(self, parser, crs):
        records = self.parse(parser)
        self.memory_layer = self._create_memory_layer(crs, self.name, self.attributes)
        self.memory_layer.add_features_from_records(records)
        return

    @classmethod
    @abc.abstractmethod
    def layer_class(cls):
        pass

    @classmethod
    def parse(cls, parser):
        return parser.advance_block(cls.attributes)

    @classmethod
    def _create_memory_layer(
        cls, crs: Any, name: str, attributes: list, layer_class=None
    ) -> QgsVectorLayer:
        fields = []
        for name in attributes:
            # Skip the coordinates.
            if name in ("x", "y", "x1", "y1", "x2", "y2", "xc", "yc"):
                continue
            # The extraction file contains exclusively real numbers, except for
            # the label column.
            elif name == "label":
                field = QgsField(name, QVariant.String)
            else:
                field = QgsField(name, QVariant.Double)
            fields.append(field)

        if layer_class is None:
            layer_class = (
                cls.layer_class()
            )  # PointMemoryLayer, LineStringMemoryLayer, etc.

        memory_layer = layer_class(name=name, crs=crs, attributes=fields)
        return memory_layer

    def write(self, path):
        newfile = not Path(path).exists()
        written = geopackage.write_layer(
            path, self.memory_layer.layer, self.name, newfile=newfile
        )
        return [written]
