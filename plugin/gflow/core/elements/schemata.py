import abc
from collections import defaultdict
from typing import Any, Dict, List, NamedTuple, Optional

from gflow.core.schemata import (
    SchemaContainer,
)


class ValidationData(NamedTuple):
    schemata: Dict[str, SchemaContainer]
    name: str
    data: Dict[str, Any]
    other: Optional[Dict[str, Any]] = None


class SchemaBase(abc.ABC):
    # TODO: check for presence of columns
    schemata: Dict[str, SchemaContainer] = {}

    @staticmethod
    def _validate_table(vd: ValidationData) -> Dict[str, List]:
        errors = defaultdict(list)
        for variable, schema in vd.schemata.items():
            _errors = schema.validate(vd.data[variable])
            if _errors:
                errors[f"{vd.name} {variable}"].extend(_errors)
        return errors

    @classmethod
    def validate_timeseries(
        cls, name: str, data: Dict[str, Any]
    ) -> Dict[str, List]:
        vd = ValidationData(cls.timeseries_schemata, (), name, data)
        return cls._validate_table(vd)

    @classmethod
    def validate(
        cls, name: str, data: Dict[str, Any]
    ) -> Dict[str, List]:
        vd = ValidationData(
            cls.schemata, name, data
        )
        return cls._validate(vd)

    @abc.abstractclassmethod
    def _validate(vd: ValidationData) -> Dict[str, List]:
        pass


class RowWiseSchema(SchemaBase, abc.ABC):
    """
    Schema for entries that should be validated row-by-row, such as Wells.
    """

    @staticmethod
    def _validate(vd: ValidationData) -> Dict[str, List]:
        errors = defaultdict(list)

        for i, row in enumerate(vd.data):
            row_errors = defaultdict(list)

            for variable, schema in vd.schemata.items():
                _errors = schema.validate(row[variable])
                if _errors:
                    row_errors[variable].extend(_errors)

            if row_errors:
                errors[f"Row {i + 1}:"] = row_errors

        return errors


class SingleRowSchema(RowWiseSchema, abc.ABC):
    """
    Schema for entries that should contain only one row, which should be
    validated as a row, such as Constant, Domain, Uniform Flow.
    """

    @staticmethod
    def _validate(vd: ValidationData) -> Dict[str, List]:
        nrow = len(vd.data)
        if nrow != 1:
            return {
                vd.name: [
                    f"Table must contain a single row. Table contains {nrow} rows."
                ]
            }
        return RowWiseSchema._validate(vd)
