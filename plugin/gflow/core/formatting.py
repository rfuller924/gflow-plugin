"""Format the content of a collection of dictionaries into GFLOW text input."""

import textwrap
from typing import Any, Dict, Tuple

import numpy as np

from gflow.widgets.compute_widget import OutputOptions


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


def headgrid_entry(domain: Dict[str, float], spacing: float) -> str:
    (xmin, xmax, ymin, ymax) = round_extent(domain, spacing)
    n_x = int((xmax - xmin) / spacing)
    return textwrap.dedent(f"""\
        window {xmin} {ymin} {xmax} {ymax}
        horizontalpoints {n_x}""")


def uniform_flow_entry(aquifer, uniflow) -> str:
    q = aquifer["conductivity"] * aquifer["thickness"] * uniflow["gradient"]
    angle = np.deg2rad(uniflow["angle"])
    qx = np.cos(angle) * q
    qy = np.sin(angle) * q
    return f"uniflow {qx} {qy}"


def first(data: dict) -> Any:
    return next(iter(data.values()))


def concat(data: dict) -> str:
    lines = []
    for value in data.values():
        lines.extend(value.rendered)
    return "\n".join(lines)


def data_to_gflow(
    gflow_data: Dict[str, Any], name: str, output_options: OutputOptions
) -> str:
    # GFLOW wants uniform flow as qx, qy
    aquifer = first(gflow_data["Aquifer"])
    uniflow = first(gflow_data["Uniform Flow"])
    domain = first(gflow_data["Domain"])
    linesinks = "\n".join(
        (
            concat(gflow_data["Head Line Sink"]),
            concat(gflow_data["Discharge Line Sink"]),
            concat(gflow_data["Drain Line Sink"]),
            concat(gflow_data["Gallery Line Sink"]),
            concat(gflow_data["Far Field Line Sink"]),
            concat(gflow_data["Lake Line Sink"]),
        )
    )

    data = {
        "name": name,
        "aquifer": aquifer.rendered[0],
        "uniflow": uniform_flow_entry(aquifer.data, uniflow.data),
        "reference": uniflow.rendered[0],
        "well": concat(gflow_data["Well"]),
        "headwell": concat(gflow_data["Head Well"]),
        "linesinks": linesinks,
        "inhomogeneity": concat(gflow_data["Inhomogeneity"]),
        "gridspec": headgrid_entry(domain.data, spacing=output_options.spacing),
    }

    content = textwrap.dedent("""
        error {name}-error.log
        yes
        message {name}-message.log
        yes
        echo {name}-echo.log
        yes
        picture off
        quit
        
        bfname {name}
        title {name}
    
        aquifer
        {aquifer}
        {uniflow}
        {reference}
        quit
        
        well
        discharge
        {well}
        quit
        
        well
        head
        {headwell}
        quit
        
        linesink
        {linesinks}
        quit
        
        inhomogeneity
        {inhomogeneity}
        quit
 
        solve 1 3 0 1
        
        grid
        {gridspec}
        plot heads
        go
        save {name}
        y
        surfer {name}
        y
        quit
        stop
    """).format(**data)
    return content
