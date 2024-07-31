import abc
from plugin.gflow.core.extract.extraction_base import Extraction
from plugin.gflow.core.memory_layer import (
    LinestringMemoryLayer,
    PolygonMemoryLayer,
    PointMemoryLayer,
)
from plugin.gflow.core import geopackage


class DoubletExtraction(Extraction, abc.ABC):
    attributes = (
        "string#",
        "conductivity",
        "width",
        "porosity",
        "wall_bottom_elevation",
        "label",
    )
    node_attributes = (
        "node#",
        "x",
        "y",
        "xc",
        "yc",
        "str_pot_jump_node",
        "parab_str_pot_jump",
        "delta_flow_cntr%",
        "delta_flow_node%",
        "label",
    )

    def __init__(self, parser, crs):
        line_records = self.parse(parser)
        node_records = self.parse_nodes(parser)

        line_x = []
        line_y = []
        for row in node_records:
            line_x.append(row["x"])
            line_y.append(row["y"])
            row["x"] = row.pop("xc")
            row["y"] = row.pop("yc")

        line_records[0]["x"] = line_x
        line_records[0]["y"] = line_y
        self.line_layer = self._create_memory_layer(crs, self.name, self.attributes)
        self.node_layer = self._create_memory_layer(
            crs, self.node_name, self.node_attributes, layer_class=PointMemoryLayer
        )
        self.line_layer.add_features_from_records(line_records)
        self.node_layer.add_features_from_records(node_records)
        return

    @classmethod
    def parse_nodes(cls, parser):
        parser.advance()  # skip another header
        node_records = parser.advance_block(cls.node_attributes)
        return node_records

    def write(self, path):
        written_line = geopackage.write_layer(
            path, self.line_layer.layer, self.name, newfile=False
        )
        written_node = geopackage.write_layer(
            path, self.node_layer.layer, self.node_name, newfile=False
        )
        return [written_line, written_node]


class OpenSlurryWallExtraction(DoubletExtraction):
    name = "gflow Open Slurry Wall"
    node_name = "gflow Open Slurry Wall Nodes"

    @classmethod
    def layer_class(cls):
        return LinestringMemoryLayer


class ClosedSlurryWallExtraction(DoubletExtraction):
    name = "gflow Closed Slurry Wall"
    node_name = "gflow Closed Slurry Wall Nodes"

    @classmethod
    def layer_class(cls):
        return PolygonMemoryLayer


class InhomogeneityExtraction(DoubletExtraction):
    name = "gflow Inhomogeneity"
    node_name = "gflow Inhomogeneity Nodes"
    attributes = (
        "string#",
        "conductivity",
        "bottom_elevation",
        "extraction_rate",
        "porosity",
        "domain_area",
        "average_potential_jump",
    )
    node_attributes = (
        "node#",
        "x",
        "y",
        "xc",
        "yc",
        "str_pot_jump_node",
        "parab_str_pot_jump",
        "real_str_extr_node",
        "imag_str_extr_node",
        "real_str_extr_cntr",
        "Ti/(Ti-T0)",
        "delta_P_node%",
        "delta_P_cntr%",
        "label",
    )

    @classmethod
    def layer_class(cls):
        return PolygonMemoryLayer
