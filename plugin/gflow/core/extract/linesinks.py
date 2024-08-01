import abc

from gflow.core.memory_layer import LinestringMemoryLayer
from gflow.core.extract.extraction_base import Extraction


class LineSinkExtraction(Extraction, abc.ABC):
    def __init__(self, parser, crs):
        records = self.parse(parser)
        for row in records:
            row["x"] = (row.pop("x1"), row.pop("x2"))
            row["y"] = (row.pop("y1"), row.pop("y2"))
        self.memory_layer = self._create_memory_layer(crs, self.name, self.attributes)
        self.memory_layer.add_features_from_records(records)
        return

    @classmethod
    def layer_class(cls):
        return LinestringMemoryLayer


class HeadLineSinkExtraction(LineSinkExtraction):
    name = "gflow Head Line Sink"
    attributes = (
        "x1",
        "y1",
        "x2",
        "y2",
        "specified_head",
        "calculated_head",
        "discharge",
        "width",
        "resistance",
        "depth",
        "baseflow",
        "overlandflow",
        "%error_BC",
        "label",
    )


class GalleryLineSinkExtraction(LineSinkExtraction):
    name = "gflow Gallery Line Sink"
    attributes = (
        "x1",
        "y1",
        "x2",
        "y2",
        "gallery_elevation",
        "calculated_water_level",
        "discharge",
        "width",
        "resistance",
        "depth",
        "%error_BC",
        "label",
    )


class DrainLineSinkExtraction(LineSinkExtraction):
    name = "gflow Line Sink"
    attributes = (
        "x1",
        "y1",
        "x2",
        "y2",
        "drainage_elevation",
        "calculated_head",
        "discharge",
        "width",
        "resistance",
        "depth",
        "%error_BC",
        "label",
    )


class DischargeLineSinkExtraction(LineSinkExtraction):
    name = "gflow Discharge Line Sink"
    attributes = (
        "x1",
        "y1",
        "x2",
        "y2",
        "discharge",
        "label",
    )
