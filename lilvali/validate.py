#!/usr/bin/env python
import inspect
import logging
from functools import partial, wraps
from itertools import chain
import pdb
from typing import (
    Any,
    Callable,
    Optional,
    Union,
)

from dataclasses import dataclass, fields
from functools import wraps

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

        self.__call__ = wraps(fn)(self)

        default_cfg = BindCheckerConfig()

        if config is not None:
            default_cfg.update(config)
            if "name" in config:
                self.name = f"_{config["name"]}"
                fn.__name__ = self.name
        else:
            self.name = fn.__name__

        self.config = default_cfg

    def __call__(self, value):
        return self.fn(value)

    def set_my_annotations(
        self, annotations: dict, return_annotation=(bool, str | None)
    ):
        self.__annotations__ = annotations
        if return_annotation is not None:
            if not isinstance(return_annotation, tuple):
                self.__annotations__["return"] = return_annotation
            else:
                self.__annotations__["return"] = return_annotation[0]
                if return_annotation[1] is not None:
                    self.config["error"] = return_annotation[1]

    def __and__(self, other: "ValidatorFunction"):
        return ValidatorFunction(lambda value: self.fn(value) and other.fn(value))

    def __or__(self, other: "ValidatorFunction") -> "ValidatorFunction":
        return ValidatorFunction(lambda value: self.fn(value) or other.fn(value))


class ValidationBindChecker(BindChecker):
    def __init__(self, config=None):
        super().__init__(config=config)
        # self.check.register(self.vf_check)
        self.register_validator(ValidatorFunction, self.vf_check)

    def vf_check(self, ann: ValidatorFunction, arg: Any):
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


class TypeValidator:
    """Callable wrapper for validating function arguments and return values."""

    def __init__(self, func: type | Callable, config=None):
        self.func = func
        if hasattr(func, "validated_base_cls"):
            self._cls = func.validated_base_cls
        else:
            log.debug("NO CLASS!")
            self._cls = None

        log.debug(f"init over {f'{self._cls}.' if self._cls is not None else ''}{self.func}")
        self.argspec, self.generics = inspect.getfullargspec(func), func.__type_params__
        log.debug(f"{func} {self.argspec=} {self.generics=}")
        self.bind_checker = ValidationBindChecker(config=config)

    def __call__(self, *args, **kwargs):
        """Validating wrapper for the bound self.func"""
        log.debug(f"CALLED: {self.func.__class__}.{self.func.__name__} called with args {args=}, {kwargs=} | {self.func.__annotations__}")
        # if the function is a method, add the class to the args.
        if "self" in self.argspec.args:
            if self._cls is not None:
                # probably init
                args = (self._cls, *args)
            log.debug(f"MfS {self.func=} {args}")
        
        # If disabled, just call the function being validated.
        if self.bind_checker.config.disabled:
            return self.func(*args, **kwargs)

        # First refresh the BindChecker with new bindings on func call,
        self.bind_checker.new_bindings(self.generics)

        fixed_args = zip(self.argspec.args, args)
        var_args = (
            (self.argspec.varargs, arg) for arg in args[len(self.argspec.args) :]
        )
        all_args = list(chain(fixed_args, var_args, kwargs.items()))
        log.debug(f"{all_args=}")
        # then check all args against their type hints.
        for name, arg in all_args:
            ann = self.argspec.annotations.get(name)
            if ann is not None:
                #print(f"{name=} {ann=} {arg=}")
                self.bind_checker.check(ann, arg)

        # After ensuring all generic values can bind,
        checked = self.bind_checker.checked
        if all(checked):
            # call the function being validated.
            result = self.func(*args, **kwargs)

            # If there is a return annotation
            if "return" in self.argspec.annotations:
                ret_ann = self.argspec.annotations["return"]
                log.debug(
                    "Return: annotations=%s result_type=%s return_spec=%s",
                    self.argspec.annotations,
                    type(result),
                    ret_ann,
                )

                # check it.
                if self.bind_checker.config.ret_validation and ret_ann is not None:
                    self.bind_checker.check(ret_ann, result)
            # Finally, return the results if nothing has gone wrong.
            return result

    def checking_on(self):
        """Turn type validation on."""
        self.bind_checker.config.disabled = False

    def checking_off(self):
        """Turn type validation off."""
        self.bind_checker.config.disabled = True


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
    log.debug(f"{func=} {config=}")

    if isinstance(config, dict):
        if not isinstance(config, BindCheckerConfig):
            config = BindCheckerConfig(**config)
    elif config is not None and not isinstance(config, BindCheckerConfig):
        raise TypeError(
            f"{config=} must be a dict or BindCheckerConfig, not {type(config)}"
        )
    else:
        config = BindCheckerConfig()

    if func is None or not callable(func):
        log.debug(f"partialling {func=}")
        return partial(validate, config=config)
    else:
        log.debug(f"wrapping {func=}")
        return wraps(func)(TypeValidator(func, config=config))


class ValidatorMeta(type):
    """ Metaclass wrapper to validate dataclasses.
    
    Ex.

    ```python
    class SomeClass(metaclass=ValidatorMeta):
    x: int
    y: str = field(default="hello")

    @validator
    def _x(value) -> bool:
        if value is not None and value > 0:
            raise ValidationError

    @validator
    def _y(value) -> bool:
        return value == "hello"
    ```
    """
    def __new__(cls, name, bases, dct):
        _cls = dataclass(super().__new__(cls, name, bases, dct))
        _cls.__init__.validated_base_cls = _cls 

        V = validate(_cls.__init__)
        _cls.__init__ = V

        for field in fields(_cls):
            vf = dct.get(f"_{field.name}")
            if isinstance(vf, ValidatorFunction):
                if "self" in inspect.getfullargspec(vf).args:
                    vf = staticmethod(vf)
                V.bind_checker.register_custom_validator(field.type, vf)


            

        return _cls
