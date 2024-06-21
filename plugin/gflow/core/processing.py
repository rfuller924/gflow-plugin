"""
Utilities for processing input or output.

Currently wraps the QGIS functions for turning grids / meshes of head results
into line contours.
"""

from pathlib import Path

import processing
from qgis.core import (
    QgsRasterLayer,
    QgsVectorLayer,
)

from gflow.core import geopackage


def raster_contours(
    gpkg_path: str,
    layer: QgsRasterLayer,
    name: str,
    start: float,
    stop: float,
    step: float,
) -> QgsVectorLayer:
    # Seemingly cannot use stop in any way, unless filtering them away.
    result = processing.run(
        "gdal:contour",
        {
            "INPUT": layer,
            "BAND": 1,
            "INTERVAL": step,
            "OFFSET": start,
            "FIELD_NAME": "head",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
    )

    path = result["OUTPUT"]
    vector_layer = QgsVectorLayer(path)
    vector_layer.setCrs(layer.crs())

    result = processing.run(
        "qgis:extractbyexpression",
        {
            "INPUT": vector_layer,
            "EXPRESSION": f'"head" >= {start} AND "head" <= {stop}',
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
    )

    newfile = not Path(gpkg_path).exists()
    written_layer = geopackage.write_layer(
        path=gpkg_path,
        layer=result["OUTPUT"],
        layername=name,
        newfile=newfile,
    )
    return written_layer
