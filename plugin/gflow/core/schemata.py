"""
Each schema enforces some constraint, e.g. it a field required or optional,
should be positive, etc.
"""
import abc
import operator
from typing import List, Union

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


class BaseSchema(abc.ABC):
    """Base class for single value."""

    def __init__(self):
        pass

    @abc.abstractmethod
    def validate(self, data) -> MaybeError:
        pass

    def validate_many(self, data) -> ErrorList:
        errors = []
        for value in data:
            error = self.validate(value)
            if error is not None:
                errors.append(error)

        return errors


class IterableSchema(abc.ABC):
    """Base class for collection of values."""

    def __init__(self, *schemata):
        self.schemata = schemata

    def validate_many(self, data) -> ErrorList:
        error = self.validate(data)
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

    def _validate_schemata(self, data) -> ErrorList:
        errors = []
        for schema in self.schemata:
            _error = schema.validate(data)
            if _error:
                errors.append(_error)
        return errors


class Optional(SchemaContainer):
    def validate(self, data) -> ErrorList:
        if data is None:
            return []
        return self._validate_schemata(data)


class Required(SchemaContainer):
    def validate(self, data) -> ErrorList:
        if data is None:
            return ["a value is required."]
        return self._validate_schemata(data)


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
