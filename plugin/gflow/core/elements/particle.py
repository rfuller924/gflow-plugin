from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsSingleSymbolRenderer

from gflow.core.elements.colors import GREY, BLACK
from gflow.core.elements.element import Element
from gflow.core.elements.schemata import RowWiseSchema
from gflow.core.schemata import (
    Optional,
    Required,
)


class ParticleSchema(RowWiseSchema):
    schemata = {
        "geometry": Required(),
        "starting_elevation": Optional(),
    }
    # TODO: validate that starting elevation is between aquifer/inhom bottom
    # and aquifer top.


class Particle(Element):
    element_type = "Forward Particle"
    geometry_type = "Point"
    attributes = (QgsField("starting_elevation", QVariant.Double),)
    schema = ParticleSchema()
    color = GREY

    @classmethod
    def renderer(cls) -> QgsSingleSymbolRenderer:
        return cls.marker_renderer(color=cls.color, size="2")

    def render(self, row):
        row = row.copy()
        row["direction"] = self.direction
        # TODO: set a default starting elevation equal to aquifer top.
        return "{x} {y} {starting_elevation} {direction}".format(**row)


class ForwardParticle(Particle):
    element_type = "Forward Particle"
    geometry_type = "Point"
    attributes = (QgsField("starting_elevation", QVariant.Double),)
    schema = ParticleSchema()
    direction = 1.0
    color = GREY


class BackwardParticle(Element):
    element_type = "Backward Particle"
    geometry_type = "Point"
    attributes = (QgsField("starting_elevation", QVariant.Double),)
    schema = ParticleSchema()
    direction = -1.0
    color = BLACK
