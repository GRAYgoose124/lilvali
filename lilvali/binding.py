from dataclasses import dataclass, field
import inspect
import logging
from functools import partial, singledispatchmethod, wraps
from itertools import chain
from types import GenericAlias, UnionType
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    TypeVar,
    _SpecialGenericAlias,
    _UnionGenericAlias,
)

from .errors import BindingError, InvalidType, ValidationError


@dataclass
class GenericBinding:
    """Represents a Generic type binding state."""

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


class BindChecker:
    """Checks if a value can bind to a type annotation given some already bound states."""

    def __init__(self):
        self.Gbinds = None

    def new_bindings(self, generics):
        self.Gbinds = {G: GenericBinding() for G in generics}

    def register_validator(self, ty, handler: Callable[[type, Any], None]):
        self.check.register(ty)(handler)

    @property
    def checked(self):
        return [val.can_bind_generic for val in self.Gbinds.values()]

    @singledispatchmethod
    def check(self, ann: Any, arg: Any, arg_types=None):
        raise ValidationError(f"Type {type(ann)} for `{arg}: {ann=}` is not handled.")

    @check.register
    def _(self, ann: TypeVar, arg: Any, arg_types=None):
        if len(ann.__constraints__) and type(arg) not in ann.__constraints__:
            raise ValidationError(
                f"{arg=} is not valid for {ann=} with constraints {ann.__constraints__}"
            )
        else:
            self.Gbinds[ann].try_bind_new_arg(arg)

    @check.register
    def _(
        self,
        ann: int | float | str | bool | bytes | type(None) | type,
        arg: Any,
        arg_types=None,
    ):
        if ann is None:
            return
        if not isinstance(arg, ann):
            raise InvalidType(f"{arg=} is not {ann=}")

    @check.register
    def _(
        self,
        ann: GenericAlias | _SpecialGenericAlias,
        arg: Any,
        arg_types=None,
    ):
        if hasattr(ann, "__args__") and len(ann.__args__):
            if issubclass(ann.__origin__, dict):
                self.check({}, arg, arg_types=ann.__args__)

        # Check the base
        # self.check(ann.__origin__, arg)

    @check.register
    def _(self, ann: list | tuple, arg: Any):
        """Handle generic sequences"""
        if len(ann) == 1:
            for a in arg:
                self.check(ann[0], a)
        elif len(ann) == len(arg):
            for a, b in zip(ann, arg):
                self.check(a, b)

    @check.register
    def _(self, ann: dict, arg: Any, arg_types=None):
        # TODO: recursive check dicts
        if not isinstance(arg, dict):
            raise ValidationError(f"{arg=} failed for dict annotation: {type(ann)}")

        if arg_types is not None:
            for k, v in arg.items():
                self.check(arg_types[0], k)
                self.check(arg_types[1], v)

    @check.register
    def _(self, ann: UnionType | _UnionGenericAlias, arg: Any, arg_types=None):
        """Handle union types"""
        for a in ann.__args__:
            try:
                # TODO: This probably will cause a bug as it could bind and then fail, leaving some bound remnants.
                self.check(a, arg)  # , update_bindings=False) # ?
                return
            except ValidationError:
                pass
        raise ValidationError(f"{arg=} failed to bind to {ann=}")
