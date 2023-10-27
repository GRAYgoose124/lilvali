#!/usr/bin/env python
import inspect
import logging
from functools import partial, wraps
from itertools import chain
from typing import (
    Any,
    Callable,
    Optional,
)

from .errors import BindingError, ValidationError, InvalidType
from .binding import BindChecker


log = logging.getLogger(__name__)


class ValidatorFunction(Callable):
    """Callable wrapper for typifying validator functions."""

    def __init__(
        self,
        fn: Callable[..., bool],
        base_type: Optional[type] = None,
        error: str = None,
    ):
        self.fn = fn
        self.base_type = base_type
        self.error = error

        self.__call__ = wraps(fn)(self)
        self.name = fn.__name__

    def __call__(self, value):
        return self.fn(value)

    def __and__(self, other: "ValidatorFunction"):
        return ValidatorFunction(lambda value: self.fn(value) and other.fn(value))

    def __or__(self, other: "ValidatorFunction") -> "ValidatorFunction":
        return ValidatorFunction(lambda value: self(value) or other(value))


class ValidationBindChecker(BindChecker):
    def __init__(self):
        super().__init__()
        self.check.register(self.vf_check)

    def vf_check(self, ann: ValidatorFunction, arg: Any, arg_types=None):
        # TODO: Fix this, exceptions r 2 slow, probably.
        # try/except to allow fallback to base_type if VF call fails
        try:
            result = ann(arg)
            if not result:
                error = ann.error
        except Exception as e:
            result = False
            error = e

        if not result:
            if ann.base_type is not None and not isinstance(arg, ann.base_type):
                raise InvalidType(f"{arg=} is not {ann.base_type=}: {error}")
            elif ann.base_type is None:
                raise ValidationError(f"{arg=} failed validation for {ann=}: {error}")


class _Validator:
    """Callable wrapper for validating function arguments and return values."""

    def __init__(self, func):
        self.func = func
        self.argspec, self.generics = inspect.getfullargspec(func), func.__type_params__
        self.bind_checker = ValidationBindChecker()

    def __call__(self, *args, **kwargs):
        # Refresh the BindChecker with new bindings on func call.
        self.bind_checker.new_bindings(self.generics)

        # check all args and kwargs together.
        for name, arg in chain(zip(self.argspec.args, args), kwargs.items()):
            ann = self.argspec.annotations.get(name)
            self.bind_checker.check(ann, arg)

        # after ensuring all values can bind
        checked = self.bind_checker.checked
        if all(checked):
            # call the function being validated
            result = self.func(*args, **kwargs)

            # if there is a return annotation
            if "return" in self.argspec.annotations:
                ret_ann = self.argspec.annotations["return"]
                log.debug(
                    "annotations=%s result_type=%s return_spec=%s",
                    self.argspec.annotations,
                    type(result),
                    ret_ann,
                )

                # check it
                self.bind_checker.check(ret_ann, result)

            # return the results if nothing has gone wrong
            return result
        else:
            # get all bad binds based on checked false indices
            bad_binds = dict(
                filter(
                    lambda x: not checked[x[0]],
                    self.bind_checker.Gbinds.items(),
                )
            )

            raise ValidationError(
                f"{self.func.__name__} failed to validate:\n{bad_binds}"
            )


def validator(func: Callable = None, *, base: Optional[type] = None, error: str = None):
    """Decorator to create custom validator functions for use in validated annotations."""
    if func is None:
        # This means the decorator was used with parentheses, like @validator(base=int)
        return partial(validator, base=base, error=error)
    else:
        return ValidatorFunction(func, base, error)


def validate(func):
    """Decorator to strictly validate function arguments and return values against their annotations."""
    validated_func = _Validator(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return validated_func(*args, **kwargs)

    return wrapper
