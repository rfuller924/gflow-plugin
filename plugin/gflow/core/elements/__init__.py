import re
from collections import defaultdict
from functools import partial
from typing import List, Tuple

from gflow.core import geopackage
from gflow.core.elements.aquifer import Aquifer
from gflow.core.elements.barrier import Barrier
from gflow.core.elements.closed_barrier import ClosedBarrier
from gflow.core.elements.domain import Domain
from gflow.core.elements.element import Element
from gflow.core.elements.flux_inspector import FluxInspector
from gflow.core.elements.headwell import HeadWell
from gflow.core.elements.inhomogeneity import Inhomogeneity
from gflow.core.elements.linesinks.discharge import DischargeLineSink
from gflow.core.elements.linesinks.drain import DrainLineSink
from gflow.core.elements.linesinks.farfield import FarFieldLineSink
from gflow.core.elements.linesinks.gallery import GalleryLineSink
from gflow.core.elements.linesinks.head import HeadLineSink
from gflow.core.elements.linesinks.lake import LakeLineSink
from gflow.core.elements.piezometer import Piezometer
from gflow.core.elements.uniform_flow import UniformFlow
from gflow.core.elements.well import Well
from gflow.core.elements.particle import ForwardParticle, BackwardParticle

ELEMENTS = {
    element.element_type: element
    for element in (
        Aquifer,
        Domain,
        UniformFlow,
        Well,
        HeadWell,
        HeadLineSink,
        DischargeLineSink,
        DrainLineSink,
        GalleryLineSink,
        FarFieldLineSink,
        LakeLineSink,
        Barrier,
        ClosedBarrier,
        Inhomogeneity,
        Piezometer,
        FluxInspector,
        ForwardParticle,
        BackwardParticle,
    )
}


def parse_name(layername: str) -> Tuple[str, str]:
    """
    Parse the name of the geopackage layer.

    Based on the layer name find out:

    * which element type it is;
    * what the user provided name is.

    For example:
    parse_name("gflow Headwell:drainage") -> ("Head Well", "drainage")
    """
    prefix, name = layername.split(":")
    element_type = re.split("gflow ", prefix)[1]
    return element_type, name


def load_elements_from_geopackage(path: str) -> List[Element]:
    # List the names in the geopackage
    gpkg_names = geopackage.layers(path)

    # Group them on the basis of name
    dd = defaultdict
    grouped_names = dd(partial(dd, list))
    for layername in gpkg_names:
        element_type, name = parse_name(layername)
        grouped_names[element_type][name] = layername

    elements = []
    for element_type, group in grouped_names.items():
        for name in group:
            elements.append(ELEMENTS[element_type](path, name))

    return elements
