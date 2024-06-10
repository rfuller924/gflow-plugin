from PyQt5.QtCore import QVariant
from qgis.core import QgsDefaultValue, QgsField
from gflow.core import geopackage
from gflow.core.elements.element import ElementExtraction, Element
from gflow.core.elements.schemata import SingleRowSchema
from gflow.core.schemata import (
    Required,
    StrictlyPositive,
)


class AquiferSchema(SingleRowSchema):
    schemata = {
        "base_elevation": Required(),
        "thickness": Required(StrictlyPositive()),
        "conductivity": Required(StrictlyPositive()),
        "porosity": Required(StrictlyPositive()),
    }


class Aquifer(Element):
    element_type = "Aquifer"
    geometry_type = "No Geometry"
    attributes = [
        QgsField("base_elevation", QVariant.Double),
        QgsField("thickness", QVariant.Double),
        QgsField("conductivity", QVariant.Double),
        QgsField("porosity", QVariant.Double),
    ]
    schema = AquiferSchema()

    def __init__(self, path: str, name: str):
        self._initialize_default(path, name)
        self.gflow_name = f"gflow {self.element_type}:Aquifer"

    def write(self):
        self.layer = geopackage.write_layer(
            self.path, self.layer, self.gflow_name, newfile=True
        )
        self.set_defaults()

    def remove_from_geopackage(self):
        """This element may not be removed."""
        return

    def to_gflow(self) -> ElementExtraction:
        missing = self.check_gflow_columns()
        if missing:
            return ElementExtraction(errors=missing)

        data = self.table_to_records(layer=self.layer)
        errors = self.schema.validate_gflow(name=self.layer.name(), data=data)
        return ElementExtraction(errors=errors, data=data)

    def extract_data(self) -> ElementExtraction:
        return self.to_gflow()
