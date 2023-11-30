#!/usr/bin/env python
import inspect, logging
from functools import partial, wraps
from typing import (
    Callable,
    Optional,
    Union,
)

from functools import wraps

from ..errors import *
from ..binding import BindCheckerConfig
from .checker import ValidatorFunction
from .validator import TypeValidator

log = logging.getLogger(__name__)


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
    target: Callable | type = None,
    *,
    config: Optional[Union[BindCheckerConfig, dict]] = None,
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
    log.debug(f"{target=} {config=}")

    def _validate_function(func, config):
        return wraps(func)(TypeValidator(func, config=config))

    def _validate_class(cls, config):
        cls.__init__.validated_base_cls = cls

        # Wrap __init__ for validation
        V = _validate_function(cls.__init__, config)
        cls.__init__ = V

        # Inspect the __init__ method to find the fields
        type_annotations = getattr(cls.__init__, "__annotations__", {})

        for arg in type_annotations:
            vf = getattr(cls, f"_{arg}", None)
            if isinstance(vf, ValidatorFunction):
                field_type = type_annotations.get(arg, None)
                if field_type:
                    V.bind_checker.register_custom_validator(field_type, vf)

        return cls

    if isinstance(config, dict):
        if not isinstance(config, BindCheckerConfig):
            config = BindCheckerConfig(**config)
    elif config is not None and not isinstance(config, BindCheckerConfig):
        raise TypeError(
            f"{config=} must be a dict or BindCheckerConfig, not {type(config)}"
        )
    else:
        config = BindCheckerConfig()

    def decorator(func_or_cls):
        if inspect.isclass(func_or_cls):
            log.debug(f"Class {func_or_cls=}")
            return _validate_class(func_or_cls, config)
        elif callable(func_or_cls):
            log.debug(f"Function {func_or_cls=}")
            return _validate_function(func_or_cls, config)
        else:
            raise TypeError("Invalid target for validation")

    if target is None:
        return decorator
    else:
        return decorator(target)
