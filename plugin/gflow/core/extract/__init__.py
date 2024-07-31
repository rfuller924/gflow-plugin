from gflow.core.extract.parser import GflowExtractParser
from gflow.core.extract.linesinks import (
    HeadLineSinkExtraction,
    DrainLineSinkExtraction,
    DischargeLineSinkExtraction,
    GalleryLineSinkExtraction,
)
from gflow.core.extract.doublets import (
    ClosedSlurryWallExtraction,
    OpenSlurryWallExtraction,
)
from gflow.core.extract.flux_inspection import FluxInspectionExtraction
from gflow.core.extract.wells import (
    HeadWellExtraction,
    DischargeWellExtraction,
    InhomogeneityExtraction,
)
from gflow.core.extract.test_point import TestPointExtraction


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
    "! flux_inspection_line_label   normal_flow        numerical_nf": FluxInspectionExtraction,
}


def extraction_to_layers(path, gpkg_path, crs):
    with open(path) as f:
        lines = f.readlines()

    parser = GflowExtractParser(lines)
    layers = []
    while not parser.done():
        line = parser.advance().strip()
        next_line = parser.peek()

        ExtractionClass = MAPPING.get(line, None)
        if ExtractionClass is None and next_line.startswith("@"):
            ExtractionClass = TestPointExtraction

        if ExtractionClass is not None:
            extraction = ExtractionClass(parser, crs)
            gpkg_layers = extraction.write(gpkg_path)
            layers.extend(gpkg_layers)

    return layers
