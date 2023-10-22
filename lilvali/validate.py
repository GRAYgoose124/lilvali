#!/usr/bin/env python
from dataclasses import dataclass, field
import inspect
import logging
from functools import singledispatchmethod, wraps
from itertools import chain
from typing import Callable, Sequence, TypeVar


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
    def can_bind(self):
        return not self.is_unbound or self.none_bound

    @property
    def is_unbound(self):
        return self.ty is None

    @property
    def none_bound(self):
        return len(self.instances) == 0

    def can_new_arg_bind(self, arg):
        return self.is_unbound or self.ty == type(arg)

    def bind_new_arg(self, arg):
        if self.is_unbound:
            self.ty = type(arg)
        elif self.ty != type(arg):
            raise BindingError(
                f"Generic bound to different types: {self.ty}, but arg is {type(arg)}"
            )
        self.instances.append(arg)


class ValidatorFunction(Callable):
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


# convert fn def to validator fn
def validator(func):
    vf = ValidatorFunction(func)
    return vf


class BindChecker:
    def __init__(self):
        self.Gbinds = None

    def new_bindings(self, generics):
        self.Gbinds = {G: GenericBinding() for G in generics}

    def check(self, ann, arg):
        if isinstance(ann, TypeVar):
            if len(ann.__constraints__) and type(arg) not in ann.__constraints__:
                raise ValidationError(
                    f"{arg=} is not valid for {ann=} with constraints {ann.__constraints__}"
                )
            ann_ty = f"{ann}:{ann.__constraints__}"
        else:
            ann_ty = type(ann).__name__

        log.debug("checking %s against %s...", arg, ann_ty)
        self._check(ann, arg)

    @singledispatchmethod
    @staticmethod
    def _check(ann, arg):
        raise ValidationError(f"Type {type(ann)} for `{arg}: {ann}` is not handled.")

    @_check.register(TypeVar)
    def _(self, ann, arg):
        self.Gbinds[ann].bind_new_arg(arg)

    @_check.register(list)
    @_check.register(tuple)
    def _(self, ann, arg):
        """Handle generic sequences"""
        # Generic tuple
        if isinstance(arg, tuple) and len(ann) == len(arg):
            for a, b in zip(ann, arg):
                self.check(a, b)
        # Generic list
        elif isinstance(arg, list):
            for a in arg:
                self.check(ann[0], a)
        else:
            raise ValidationError(f"{arg=} is not valid for {ann=}")

    @_check.register(ValidatorFunction)
    @staticmethod
    def _(ann, arg):
        if not ann(arg):
            raise ValidationError(
                f"{arg=} is not valid for {ann.__name__ if '__name__' in dir(ann) else ann=}"
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
            annotation = self.argspec.annotations.get(name)
            if annotation is not None:
                self.bind_checker.check(annotation, arg)

        # after ensuring all values can bind
        if all(val.can_bind for val in self.bind_checker.Gbinds.values()):
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
            raise ValidationError(f"{self.bind_checker.Gbinds=}")


def validate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return Validator(func)(*args, **kwargs)

    return wrapper
