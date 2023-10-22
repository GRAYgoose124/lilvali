#!/usr/bin/env python
from dataclasses import dataclass, field
import inspect
import logging
from functools import partial, singledispatchmethod, wraps
from itertools import chain
from typing import Callable, Optional, TypeVar


log = logging.getLogger(__name__)


class ValidationError(TypeError):
    pass


class InvalidType(ValidationError):
    pass


class BindingError(ValidationError):
    pass


@dataclass
class GenericBinding:
    ty: type = None
    instances: list = field(default_factory=list)

    @property
    def is_bound(self):
        """True if the GenericBinding is unbound"""
        return self.ty is not None

    @property
    def none_bound(self):
        return len(self.instances) == 0

    @property
    def can_bind_generic(self):
        """True if the GenericBinding can bind to a new arg."""
        return self.is_bound or self.none_bound

    def can_new_arg_bind(self, arg):
        """True if a given arg can be bound to the current GenericBinding context."""
        return not self.is_bound or self.ty == type(arg)

    def try_bind_new_arg(self, arg):
        if self.can_new_arg_bind(arg):
            self.ty = type(arg)
            self.instances.append(arg)
        else:
            raise BindingError(
                f"Generic bound to different types: {self.ty}, but arg is {type(arg)}"
            )


class ValidatorFunction(Callable):
    def __init__(self, fn, base_type: Optional[type] = None):
        self.fn = fn
        self.base_type = base_type

    def __call__(self, value):
        return self.fn(value)


def validator(func: Callable = None, *, base: Optional[type] = None):
    if func is None:
        # This means the decorator was used with parentheses, like @validator(base=int)
        return wraps(func)(partial(validator, base=base))
    else:
        return wraps(func)(ValidatorFunction(func, base))


class BindChecker:
    def __init__(self):
        self.Gbinds = None

    def new_bindings(self, generics):
        self.Gbinds = {G: GenericBinding() for G in generics}

    @property
    def checked(self):
        return [val.can_bind_generic for val in self.Gbinds.values()]

    @singledispatchmethod
    def check(self, ann, arg):
        raise ValidationError(f"Type {type(ann)} for `{arg}: {ann}` is not handled.")

    @check.register(TypeVar)
    def _(self, ann, arg):
        if len(ann.__constraints__) and type(arg) not in ann.__constraints__:
            raise ValidationError(
                f"{arg=} is not valid for {ann=} with constraints {ann.__constraints__}"
            )
        else:
            self.Gbinds[ann].try_bind_new_arg(arg)

    @check.register(list)
    @check.register(tuple)
    def _(self, ann, arg):
        """Handle generic sequences"""
        if len(ann) == 1:
            for a in arg:
                self.check(ann[0], a)
        elif len(ann) == len(arg):
            for a, b in zip(ann, arg):
                self.check(a, b)

    @check.register(ValidatorFunction)
    @staticmethod
    def _(ann, arg):
        if ann.base_type is not None and not isinstance(arg, ann.base_type):
            raise InvalidType(f"{arg=} is not {ann.base_type=}")

        # TODO: Fix this, exceptions r 2 slow, probably.
        # try/except to allow fallback to base_type if VF call fails
        try:
            if not ann(arg):
                raise ValidationError(f"{arg=} failed validation for {ann=}")
        except Exception as e:
            if ann.base_type is None:
                raise ValidationError(
                    f"{arg=} raised an exception during validation for {ann=}: {str(e)}"
                )


class Validator:
    def __init__(self, func):
        self.func = func
        self.argspec, self.generics = inspect.getfullargspec(func), func.__type_params__
        self.bind_checker = BindChecker()

    def __call__(self, *args, **kwargs):
        # Refresh the BindChecker with new bindings on func call.
        self.bind_checker.new_bindings(self.generics)

        # check all args and kwargs together.
        for name, arg in chain(zip(self.argspec.args, args), kwargs.items()):
            ann = self.argspec.annotations.get(name)
            if ann is not None:
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
                # and the return annotation is not simply the type
                if ret_ann != type(result):
                    # check the return annotation
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


def validate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return Validator(func)(*args, **kwargs)

    return wrapper
