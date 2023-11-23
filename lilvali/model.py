import logging, os, inspect, unittest
from dataclasses import dataclass, fields, field
from functools import wraps

from lilvali import validate, validator, ValidationError, ValidatorFunction


log = logging.getLogger(__name__)


class ValidatorMeta(type):
    def __new__(cls, name, bases, dct):
        _cls = dataclass(super().__new__(cls, name, bases, dct))

        _cls._validators = {}
        for field in fields(_cls):
            validator = dct.get(field.name)
            if isinstance(validator, ValidatorFunction):
                _cls._validators[field.name] = validator

        return _cls


class ValidateField:
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value):
        validator = obj._validators.get(self.name)
        if validator:
            value = validator(value)
        obj.__dict__[self.name] = value


class ValidationModel(metaclass=ValidatorMeta):
    def __setattr__(self, name, value):
        validator = self._validators.get(name)
        if validator:
            value = validator(value)
        super().__setattr__(name, value)


VM = ValidationModel
