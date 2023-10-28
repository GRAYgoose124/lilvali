#!/usr/bin/env python
import inspect
import logging
from functools import partial, wraps
from itertools import chain
from typing import (
    Any,
    Callable,
    Optional,
    Union,
)

from .errors import BindingError, ValidationError, InvalidType
from .binding import BindChecker, BindCheckerConfig


log = logging.getLogger(__name__)


class ValidatorFunction(Callable):
    """Callable wrapper for typifying validator functions."""

    def __init__(
        self,
        fn: Callable[..., bool],
        base_type: Optional[type] = None,
        config: Optional[dict] = None,
    ):
        self.fn = fn
        self.base_type = base_type
        self.config = config or {"strict": False, "error": ""}

        self.__call__ = wraps(fn)(self)
        self.name = fn.__name__

    def __call__(self, value):
        return self.fn(value)

    def __and__(self, other: "ValidatorFunction"):
        return ValidatorFunction(lambda value: self.fn(value) and other.fn(value))

    def __or__(self, other: "ValidatorFunction") -> "ValidatorFunction":
        return ValidatorFunction(lambda value: self.fn(value) or other.fn(value))


class ValidationBindChecker(BindChecker):
    def __init__(self, config=None):
        super().__init__(config)
        self.check.register(self.vf_check)

    def vf_check(self, ann: ValidatorFunction, arg: Any, arg_types=None):
        # TODO: Fix this, exceptions r 2 slow, probably.
        # try/except to allow fallback to base_type if VF call fails
        try:
            result = ann(arg)
            if not result:
                error = ann.config["error"]
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

    def __init__(self, func, config=None):
        self.func = func
        self.argspec, self.generics = inspect.getfullargspec(func), func.__type_params__
        self.bind_checker = ValidationBindChecker(config=config)

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


def validator(func: Callable = None, *, base: Optional[type] = None, **config):
    """Decorator to create custom validator functions for use in validated annotations.

    Can optionally take a base type to check against if the validator function fails.

    ```python
    @validator(base=int)
    def has_c_or_int(arg):
        return True if "c" in arg else False
    ```
    """
    if func is None or not callable(func):
        return partial(validator, base=base, config=config)
    else:
        return ValidatorFunction(func, base, config)


def validate(
    func: Callable = None, *, config: Optional[Union[BindCheckerConfig, dict]] = None
):
    """Decorator to strictly validate function arguments and return values against their annotations.

    Can optionally take a config dict to change the behavior of the validator.

    ```python
    @validate
    def func(a: int, b: str) -> str:
        return b * a

    @validate(config={"strict": False})
    def func(a: int, b: str) -> str:
        return b * a
    ```
    """

    if isinstance(config, dict):
        config = BindCheckerConfig(**config)

    if func is None or not callable(func):
        return partial(validate, config=config)
    else:
        validated_func = _Validator(func, config=config)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return validated_func(*args, **kwargs)

        return wrapper
