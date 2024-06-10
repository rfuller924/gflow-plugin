"""
Format the content of a collection of dictionaries into GFLOW text input.
"""

import pprint
import re
import textwrap
from typing import Any, Dict, Tuple

import numpy as np

from gflow.widgets.compute_widget import OutputOptions

GFLOW_MAPPING = {
    "Constant": "Constant",
    "Uniform Flow": "Uflow",
    "Circular Area Sink": "CircAreaSink",
    "Well": "Well",
    "Head Well": "HeadWell",
    "Remote Head Well": "HeadWell",
    "Polygon Inhomogeneity": "PolygonInhomMaq",
    "Polygon Area Sink": "PolygonInhomMaq",
    "Polygon Semi-Confined Top": "PolygonInhomMaq",
    "Head Line Sink": "HeadLineSinkString",
    "Line Sink Ditch": "LineSinkDitchString",
    "Leaky Line Doublet": "LeakyLineDoubletString",
    "Impermeable Line Doublet": "ImpLineDoubletString",
    "Building Pit": "BuildingPit",
    "Leaky Building Pit": "LeakyBuildingPit",
    "Head Observation": "Head Observation",
    "Discharge Observation": "Discharge Observation",
}
PREFIX = "    "



def sanitized(name: str) -> str:
    return name.split(":")[-1].replace(" ", "_")


def format_kwargs(data: Dict[str, Any]) -> str:
    return textwrap.indent(
        "\n".join(f"{k}={pprint.pformat(v)}," for k, v in data.items()), prefix=PREFIX
    )


def round_spacing(ymin: float, ymax: float) -> float:
    """
    Some reasonable defaults for grid spacing.

    We attempt to get around 50 rows in the computed grid, with grid sizes a
    multiple of 1.0, 5.0, 50.0, or 500.0.
    """
    dy = (ymax - ymin) / 50.0
    if dy > 500.0:
        dy = round(dy / 500.0) * 500.0
    elif dy > 50.0:
        dy = round(dy / 50.0) * 50.0
    elif dy > 5.0:  # round to five
        dy = round(dy / 5.0) * 5.0
    elif dy > 1.0:
        dy = round(dy)
    return dy


def round_extent(domain: Dict[str, float], spacing: float) -> Tuple[float]:
    """
    Increases the extent until all sides lie on a coordinate
    divisible by spacing.

    Parameters
    ----------
    extent: Tuple[float]
        xmin, xmax, ymin, ymax
    spacing: float
        Desired cell size of the output head grids

    Returns
    -------
    extent: Tuple[float]
        xmin, xmax, ymin, ymax
    """
    xmin = domain["xmin"]
    ymin = domain["ymin"]
    xmax = domain["xmax"]
    ymax = domain["ymax"]
    xmin = np.floor(xmin / spacing) * spacing
    ymin = np.floor(ymin / spacing) * spacing
    xmax = np.ceil(xmax / spacing) * spacing
    ymax = np.ceil(ymax / spacing) * spacing
    xmin += 0.5 * spacing
    xmax += 0.5 * spacing
    ymax -= 0.5 * spacing
    xmin -= 0.5 * spacing
    return xmin, xmax, ymin, ymax


def headgrid_entry(domain: Dict[str, float], spacing: float) -> Dict[str, float]:
    (xmin, xmax, ymin, ymax) = round_extent(domain, spacing)
    return {
        "xmin": xmin,
        "xmax": xmax,
        "ymin": ymin,
        "ymax": ymax,
        "spacing": spacing,
    }


def json_elements_and_observations(data, mapping: Dict[str, str]):
    aquifer_data = data.pop("gflow Aquifer:Aquifer")

    observations = {}
    discharge_observations = {}
    gflow_data = {"Aquifer": aquifer_data}
    for layername, element_data in data.items():
        prefix, name = layername.split(":")
        plugin_name = re.split("gflow ", prefix)[1]
        gflow_name = mapping[plugin_name]
        if gflow_name is None:
            continue

        entry = {"name": name, "data": element_data}
        gflow_data[layername] = entry

    return gflow_data, observations, discharge_observations


def gflow_json(
    timml_data: Dict[str, Any],
    output_options: OutputOptions,
) -> Dict[str, Any]:
    """
    Take the data and add:

    * the TimML type
    * the layer name

    Parameters
    ----------
    data: Dict[str, Any]
    output_options: OutputOptions

    Returns
    -------
    json_data: Dict[str, Any]
        Data ready to dump to JSON.
    """
    # Process TimML elements
    data = timml_data.copy()  # avoid side-effects
    domain_data = data.pop("gflow Domain:Domain")
    elements, observations, discharge_observations = json_elements_and_observations(
        data, mapping=GFLOW_MAPPING
    )
    json_data = {
        "gflow": elements,
        "observations": observations,
        "discharge_observations": discharge_observations,
        "window": domain_data,
        "output_options": output_options._asdict(),
    }
    if output_options.mesh or output_options.raster:
        json_data["headgrid"] = headgrid_entry(domain_data, output_options.spacing)
    return json_data



def data_to_json(
    gflow_data: Dict[str, Any],
    output_options: OutputOptions,
) -> Dict[str, Any]:
    return gflow_json(gflow_data, output_options)
