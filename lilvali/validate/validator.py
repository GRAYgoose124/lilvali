import inspect, logging
from itertools import chain
from typing import (
    Callable,
)


from .checker import ValidationBindChecker


log = logging.getLogger(__name__)


class TypeValidator:
    """Callable wrapper for validating function arguments and return values."""

    def __init__(self, func: type | Callable, config=None):
        self.func = func
        if hasattr(func, "validated_base_cls"):
            self._cls = func.validated_base_cls
        else:
            log.debug("NO CLASS!")
            self._cls = None

        log.debug(
            f"init over {f'{self._cls}.' if self._cls is not None else ''}{self.func}, {func.__type_params__}"
        )
        self.argspec, self.generics = inspect.getfullargspec(func), func.__type_params__
        log.debug(f"{func} {self.argspec=} {self.generics=}")
        self.bind_checker = ValidationBindChecker(config=config)

    def __call__(self, *args, **kwargs):
        """Validating wrapper for the bound self.func"""
        log.debug(
            f"CALLED: {self.func.__class__}.{self.func.__name__} called with args {args=}, {kwargs=} | {self.func.__annotations__}"
        )
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
                # print(f"{name=} {ann=} {arg=}")
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
