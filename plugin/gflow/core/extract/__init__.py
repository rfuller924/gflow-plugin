"""
Read the GFLOW extract (.XTR) file and convert its results to GeoPackage vector
layers.
"""

from gflow.core.extract.linesinks import (
    HeadLineSinkExtraction,
    DrainLineSinkExtraction,
    DischargeLineSinkExtraction,
    GalleryLineSinkExtraction,
)
from gflow.core.extract.doublets import (
    ClosedSlurryWallExtraction,
    OpenSlurryWallExtraction,
    InhomogeneityExtraction,
)

# from gflow.core.extract.flux_inspection import FluxInspectionExtraction
from gflow.core.extract.wells import (
    HeadWellExtraction,
    DischargeWellExtraction,
)
from gflow.core.extract.test_point import TestPointExtraction


# Mapping from header to data type.
MAPPING = {
    "! discharge specified wells": DischargeWellExtraction,
    "! head specified wells": HeadWellExtraction,
    "! discharge specified line sinks": DischargeLineSinkExtraction,
    "! head specified line sinks": HeadLineSinkExtraction,
    "! drains": DrainLineSinkExtraction,
    "! galleries": GalleryLineSinkExtraction,
    "! transmissivity inhomogeneity domain.": InhomogeneityExtraction,
    "! open slurry wall.": OpenSlurryWallExtraction,
    "! closed slurry wall.": ClosedSlurryWallExtraction,
    "*      x              y              z          porosity    hydr. conduct.   base elevation net recharge  leakage (bottom)      head      lower head     resistance                   Vx                    Vy                    Vz              label": TestPointExtraction,
    #    "! flux_inspection_line_label   normal_flow        numerical_nf": FluxInspectionExtraction,
}


class GflowExtractParser:
    def __init__(self, lines: list[str]):
        self.lines = lines
        self.count = 0
        self.n = len(lines)

    def peek(self) -> str:
        return self.lines[self.count]

    def advance(self) -> str:
        line = self.peek()
        self.count += 1
        return line

    def done(self) -> bool:
        return self.count >= (self.n - 1)

    @staticmethod
    def _end_of_block(line) -> bool:
        return line.startswith("*") or line.startswith("!")

    def advance_block(self, attributes) -> list[dict]:
        line = self.peek()
        records = []
        while not self._end_of_block(line):
            line = self.advance()[1:]
            record = {}
            for key, value in zip(attributes, line.split(",")):
                # GFLOW seems to write null bytes in some places
                value = value.strip().replace("\x00", "")
                # The XTR file contains almost solely floating point values.
                # The exception is the labels, which should remain a string.
                if key == "label":
                    record[key] = value
                else:
                    try:
                        record[key] = float(value)
                    except ValueError:
                        record[key] = None
            records.append(record)
            line = self.peek()
        return records


def extraction_to_layers(path, crs, gpkg_path):
    with open(path) as f:
        lines = f.readlines()

    parser = GflowExtractParser(lines)
    layers = []
    while not parser.done():
        line = parser.advance().strip()
        ExtractionClass = MAPPING.get(line, None)
        if ExtractionClass is not None:
            extraction = ExtractionClass(parser, crs)
            # TODO: set layer styling
            gpkg_layers = extraction.write(gpkg_path)
            layers.extend(gpkg_layers)

    return layers
