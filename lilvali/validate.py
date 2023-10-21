#!/usr/bin/env python
from dataclasses import dataclass, field
import inspect
import logging
from functools import wraps
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
        return self.ty is not None or len(self.instances) == 0


class BindChecker:
    def __init__(self):
        self.handlers = {
            TypeVar: self.handle_typevar,
            (list, tuple): self.handle_sequence,
            Callable: self.handle_callable,
        }
        self.Gbinds = None

    def register_handler(self, type_check, handler):
        self.handlers[type_check] = handler

    def check(self, ann, arg):
        if isinstance(ann, TypeVar):
            if len(ann.__constraints__) and type(arg) not in ann.__constraints__:
                raise ValidationError(
                    f"{arg=} is not valid for {ann=} with constraints {ann.__constraints__}"
                )
            ann_ty = f"{ann}:ann.__constraints__"
        else:
            ann_ty = type(ann).__name__

        log.debug(f"{ann=}:{ann_ty} {arg=} {self.Gbinds=}")

        for type_check, handler in self.handlers.items():
            if isinstance(type_check, Sequence):
                if any(isinstance(ann, t) for t in type_check):
                    handler(ann, arg)
                    return
            elif isinstance(ann, type_check):
                handler(ann, arg)
                return

        raise ValidationError(f"Type {type(ann)} is not handled.")

    def handle_typevar(self, ann, arg):
        if self.Gbinds[ann].ty is None:
            self.Gbinds[ann].ty = type(arg)
        elif self.Gbinds[ann].ty != type(arg):
            raise ValidationError(
                f"Generic {ann} bound to different types: {self.Gbinds[ann].ty}, but arg is {type(arg)}"
            )
        self.Gbinds[ann].instances.append(arg)

    def handle_sequence(self, ann, arg):
        if isinstance(arg, tuple) and len(ann) == len(arg):
            for a, b in zip(ann, arg):
                self.check(a, b)
        elif isinstance(arg, list):
            for a in arg:
                self.check(ann[0], a)
        else:
            raise ValidationError(f"{arg=} is not valid for {ann=}")

    def handle_callable(self, ann, arg):
        if not ann(arg):
            raise ValidationError(f"{arg=} is not valid for {ann.__name__}")


class Validator:
    def __init__(self, func):
        self.func = func
        self.argspec, self.generics = inspect.getfullargspec(func), func.__type_params__
        self.bind_checker = BindChecker()

    def __call__(self, *args, **kwargs):
        self.bind_checker.Gbinds = {G: GenericBinding() for G in self.generics}
        for name, arg in chain(zip(self.argspec.args, args), kwargs.items()):
            annotation = self.argspec.annotations.get(name)
            if annotation is not None:
                self.bind_checker.check(annotation, arg)

        if all(val.can_bind for val in self.bind_checker.Gbinds.values()):
            result = self.func(*args, **kwargs)

            if "return" in self.argspec.annotations:
                ret_ann = self.argspec.annotations["return"]
                log.debug(
                    "annotations=%s result_type=%s return_spec=%s",
                    self.argspec.annotations,
                    type(result),
                    ret_ann,
                )
                if ret_ann != type(result):
                    self.bind_checker.check(ret_ann, result)

            return result
        else:
            raise ValidationError(f"{self.bind_checker.Gbinds=}")


def validate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return Validator(func)(*args, **kwargs)

    return wrapper
