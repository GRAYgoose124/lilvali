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


def check_binding(ann, arg, Gbinds):
    if isinstance(ann, TypeVar):
        if len(ann.__constraints__) and type(arg) not in ann.__constraints__:
            raise ValidationError(
                f"{arg=} is not valid for {ann=} with constraints {ann.__constraints__}"
            )
        ann_ty = f"{ann}:ann.__constraints__"
    else:
        ann_ty = type(ann).__name__

    log.debug(f"{ann=}:{ann_ty} {arg=} {Gbinds=}")

    def handle_typevar():
        if Gbinds[ann].ty is None:
            Gbinds[ann].ty = type(arg)
        elif Gbinds[ann].ty != type(arg):
            raise ValidationError(
                f"Generic {ann} bound to different types: {Gbinds[ann].ty}, but arg is {type(arg)}"
            )
        Gbinds[ann].instances.append(arg)

    def handle_sequence():
        if isinstance(arg, tuple) and len(ann) == len(arg):
            for a, b in zip(ann, arg):
                check_binding(a, b, Gbinds)
        elif isinstance(arg, list):
            for a in arg:
                check_binding(ann[0], a, Gbinds)
        else:
            raise ValidationError(f"{arg=} is not valid for {ann=}")

    def handle_callable():
        if not ann(arg):
            raise ValidationError(f"{arg=} is not valid for {ann.__name__}")

    type_handlers = {
        TypeVar: handle_typevar,
        (list, tuple): handle_sequence,
        Callable: handle_callable,
    }

    for type_check, handler in type_handlers.items():
        if isinstance(type_check, Sequence):
            if any(isinstance(ann, t) for t in type_check):
                handler()
                return
        elif isinstance(ann, type_check):
            handler()
            return

    raise ValidationError(f"Type {type(ann)} is not handled.")


def validate(func):
    """Validate the arguments of a function."""
    argspec, generics = inspect.getfullargspec(func), func.__type_params__

    @wraps(func)
    def wrapper(*args, **kwargs):
        Gbinds = {G: GenericBinding() for G in generics}

        for name, arg in chain(zip(argspec.args, args), kwargs.items()):
            annotation = argspec.annotations.get(name)
            if annotation is not None:
                check_binding(annotation, arg, Gbinds)

        if all(val.can_bind for val in Gbinds.values()):
            result = func(*args, **kwargs)

            if "return" in argspec.annotations:
                ret_ann = argspec.annotations["return"]
                log.debug(
                    "annotations=%s result_type=%s return_spec=%s",
                    argspec.annotations,
                    type(result),
                    ret_ann,
                )

                if ret_ann != type(result):
                    check_binding(ret_ann, result, Gbinds)

            return result
        else:
            raise ValidationError(f"{Gbinds=}")

    return wrapper
