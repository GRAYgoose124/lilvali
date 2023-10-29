from dataclasses import dataclass, field
from functools import singledispatchmethod
import types
import typing
import logging
from typing import (
    Any,
    Callable,
    Optional,
)

from .errors import BindingError, InvalidType, ValidationError


log = logging.getLogger(__name__)


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


@dataclass
class BindCheckerConfig:
    strict: bool = True
    implied_lambdas: bool = False
    ret_validation: bool = True
    disabled: bool = False


class BindChecker:
    """Checks if a value can bind to a type annotation given some already bound states."""

    def __init__(self, config: Optional[dict] = None):
        self.Gbinds = None
        self.config = config or BindCheckerConfig()

    def new_bindings(self, generics):
        self.Gbinds = {G: GenericBinding() for G in generics}

    def register_validator(self, ty, handler: Callable[[type, Any], None]):
        """Register a handler for a type annotation."""
        self.check.register(ty)(handler)

    @property
    def checked(self):
        return [val.can_bind_generic for val in self.Gbinds.values()]

    @singledispatchmethod
    def check(
        self,
        ann: int | float | str | bool | bytes | type(None) | type | typing._AnyMeta,
        arg: Any,
        arg_types=None,
    ):
        if ann is None:
            return

        if type(ann) == typing._AnyMeta:
            if self.config.strict:
                raise ValidationError(
                    f"Type {type(ann)} for `{arg}: {ann=}` must be validated, it cannot be left un-annotated! Disable strict validation to allow this."
                )
            else:
                return

        if not isinstance(arg, ann):
            raise InvalidType(f"{ann=} can not validate {arg=}")

    @check.register
    def _(
        self,
        ann: types.GenericAlias | typing._GenericAlias | typing._SpecialGenericAlias,
        arg: Any,
        arg_types=None,
    ):
        if hasattr(ann, "__args__") and len(ann.__args__):
            if issubclass(ann.__origin__, dict):
                self.check({}, arg, arg_types=ann.__args__)

        # Check the base
        # self.check(ann.__origin__, arg)

    @check.register
    def _(self, ann: typing.TypeVar, arg: Any, arg_types=None):
        if len(ann.__constraints__) and type(arg) not in ann.__constraints__:
            raise ValidationError(
                f"{arg=} is not valid for {ann=} with constraints {ann.__constraints__}"
            )
        else:
            self.Gbinds[ann].try_bind_new_arg(arg)

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
        if arg_types is not None:
            for k, v in arg.items():
                self.check(arg_types[0], k)
                self.check(arg_types[1], v)

    @check.register
    def _(
        self, ann: types.UnionType | typing._UnionGenericAlias, arg: Any, arg_types=None
    ):
        """Handle union types"""
        for a in ann.__args__:
            try:
                # TODO: This probably will cause a bug as it could bind and then fail, leaving some bound remnants.
                self.check(a, arg)  # , update_bindings=False) # ?
                return
            except ValidationError:
                pass
        raise ValidationError(f"{arg=} failed to bind to {ann=}")

    @check.register
    def _(self, ann: typing._TypedDictMeta, arg: Any, arg_types=None):
        """Handle TypedDicts"""
        arg_types = arg_types or ann.__annotations__

        for k, v in arg.items():
            self.check(arg_types[k], v)

    @check.register
    def _(self, ann: typing._LiteralGenericAlias, arg: Any, arg_types=None):
        """Handle Literal types"""
        if arg not in ann.__args__:
            raise ValidationError(f"{arg=} failed to bind to {ann=}")

    @check.register
    def _(self, ann: typing._CallableGenericAlias, arg: Any, arg_types=None):
        """Handle Callable types"""
        if not callable(arg):
            raise ValidationError(f"{arg=} failed to bind to {ann=}")
        else:
            if len(ann.__args__):
                if arg.__name__ == "<lambda>" and not self.config.implied_lambdas:
                    raise ValidationError(
                        f"lambda {arg=} cannot have the required annotations, use a def"
                    )

                if hasattr(arg, "__annotations__"):
                    ann_args = {
                        k: v for (k, v) in arg.__annotations__.items() if k != "return"
                    }
                    ann_ret = arg.__annotations__.get("return")

                    if ann_ret is not None:
                        # Assuming return type is the last in __args__
                        self.check(ann_ret, ann.__args__[-1]())

                    if len(ann_args):
                        for idx, (arg_name, arg_type) in enumerate(ann_args.items()):
                            expected_type = ann.__args__[idx]
                            self.check(expected_type, arg_type())
