import logging
from functools import wraps
from typing import (
    Any,
    Callable,
    Optional,
)


from ..errors import *
from ..binding import BindChecker, BindCheckerConfig


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
                self.name = f"_{config['name']}"
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
        def wrapper(value):
            try:
                result = self.fn(value)
            except ValidationError as e:
                result = False

            result |= other.fn(value)

            return result

        return ValidatorFunction(wrapper)


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
