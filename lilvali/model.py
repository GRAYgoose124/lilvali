import logging, os, inspect, unittest
from dataclasses import dataclass, fields, field
from functools import wraps

from lilvali import validate, validator, ValidationError, ValidatorFunction
from lilvali.validate import TypeValidator

log = logging.getLogger(__name__)


# TODO: hack, should be using lilvali.validate not validator.
class ValidatorMeta(type):
    def __new__(cls, name, bases, dct):
        _cls = dataclass(super().__new__(cls, name, bases, dct))

        # these custom validators should be part of a real _Validator.
        # print(_cls.__name__, _cls.__init__.__annotations__)
        V = validate(_cls.__init__)
        _cls.__init__ = V
        for field in fields(_cls):
            vf = dct.get(f"_{field.name}")
            # print(dct)
            # set function annotations to be equal to the field's type
            if isinstance(vf, ValidatorFunction):
                V.bind_checker.register_validator(field.type, vf)

        return _cls


class ValidationModel(metaclass=ValidatorMeta):
    pass


VM = ValidationModel
