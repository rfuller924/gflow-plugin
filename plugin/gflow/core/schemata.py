import abc
import operator
from typing import Any, Dict, List, Sequence, Union

OPERATORS = {
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    ">": operator.gt,
}


MaybeError = Union[None, str]
ErrorList = List[str]


def format(data) -> str:
    return ", ".join(map(str, data))


# Base classes


class BaseSchema(abc.ABC):
    """Base class for single value."""

    def __init__(self):
        pass

    @abc.abstractmethod
    def validate(self, data, other) -> MaybeError:
        pass

    def validate_many(self, data, other) -> ErrorList:
        errors = []
        for value in data:
            error = self.validate(value, other)
            if error is not None:
                errors.append(error)

        return errors


class IterableSchema(abc.ABC):
    """Base class for collection of values."""

    def __init__(self, *schemata):
        self.schemata = schemata

    def validate_many(self, data, other) -> ErrorList:
        error = self.validate(data, other)
        if error:
            return [error]
        else:
            return []


class SchemaContainer(abc.ABC):
    def __init__(self, *schemata):
        self.schemata = schemata

    @abc.abstractmethod
    def validate(self):
        pass

    def _validate_schemata(self, data, other=None) -> ErrorList:
        errors = []
        for schema in self.schemata:
            _error = schema.validate(data, other)
            if _error:
                errors.append(_error)
        return errors


class Optional(SchemaContainer):
    def validate(self, data, other=None) -> ErrorList:
        if data is None:
            return []
        return self._validate_schemata(data, other)


class Required(SchemaContainer):
    def validate(self, data, other=None) -> ErrorList:
        if data is None:
            return ["a value is required."]
        return self._validate_schemata(data, other)


class Positive(BaseSchema):
    def validate(self, data, _=None) -> MaybeError:
        if data < 0:
            return f"Number is not positive (>=0): {data}"
        return None


class StrictlyPositive(BaseSchema):
    def validate(self, data, _=None) -> MaybeError:
        if data <= 0:
            return f"Number is not strictly positive (>0): {data}"
        return None


class SingleRow(SchemaContainer):
    def validate(self, data, _=None) -> MaybeError:
        nrow = len(data)
        if nrow != 1:
            return f"Table must contain one row, found {nrow} rows."
        return None
