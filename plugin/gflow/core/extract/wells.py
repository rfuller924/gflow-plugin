from gflow.core.extract.extraction_base import Extraction
from gflow.core.memory_layer import PointMemoryLayer


class WellExtraction(Extraction):
    @classmethod
    def layer_class(cls):
        return PointMemoryLayer


class DischargeWellExtraction(WellExtraction):
    name = "gflow Discharge Well"
    attributes = ("x", "y", "radius", "Q", "head", "label")


class HeadWellExtraction(WellExtraction):
    name = "gflow Head Well"
    attributes = ("x", "y", "radius", "Q", "head", "%error_in_head", "label")
