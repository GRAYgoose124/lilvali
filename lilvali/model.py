import logging, os, inspect, unittest
from dataclasses import dataclass, fields, field
from functools import wraps

from lilvali import validate, validator, ValidationError, ValidatorFunction
from lilvali.validate import _Validator

log = logging.getLogger(__name__)


class ValidatorMeta(type):
    def __new__(cls, name, bases, dct):
        _cls = dataclass(super().__new__(cls, name, bases, dct))

        _cls._validators = {}
        _cls._config = {}
        for field in fields(_cls):
            validator = dct.get(field.name)
            # set function annotations to be equal to the field's type
            if isinstance(validator, ValidatorFunction):
                validator.set_my_annotations({"value": field.type})
                _cls._validators[field.name] = validator

        return _cls


class ValidationModel(metaclass=ValidatorMeta):
    def __setattr__(self, name, value):
        validator = self._validators.get(name)
        if validator is not None and not validator(value):
            raise ValidationError(f"Invalid value for {name}: {value}")
        super().__setattr__(name, value)


VM = ValidationModel
