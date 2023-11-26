from dataclasses import dataclass, field
from functools import singledispatchmethod
import types, typing, logging
from typing import (
    Any,
    Callable,
)


from ..errors import *
from .struct import GenericBindings
from .config import BindCheckerConfig


log = logging.getLogger(__name__)


class BindChecker:
    """Checks if a value can bind to a type annotation given some already bound states."""

    def __init__(self, config: dict | BindCheckerConfig):
        self.Gbinds = None
        self.config = config

        self.custom_validators = {}

    def new_bindings(self, generics):
        self.Gbinds = GenericBindings(generics)

    def register_validator(self, ty, handler: Callable[[type, Any], None]):
        """Register a handler for a type annotation."""
        self.check.register(ty)(handler)
        log.debug(f"Registered {handler=} for {ty=}")

    def register_custom_validator(self, ty, handler: Callable[[type, Any], None]):
        """Register a handler for a type annotation.

        Could be part of register validator, but there are many catches to custom validation.
            Should only use on primitive types.
        """
        self.custom_validators.setdefault(ty, []).append(handler)
        log.debug(f"Registered custom {handler=} for {ty=}")

    @property
    def checked(self):
        return [val.can_bind_generic for val in self.Gbinds.values()]

    def __check_with_custom_validators(self, ty, value):
        """Check a value against custom validators."""
        if not self.config.use_custom_validators:
            return

        if ty in self.custom_validators:
            for handler in self.custom_validators[ty]:
                valid = handler(value)
                if valid is not None and not valid:
                    raise ValidationError(f"{value=} failed to bind to {ty=}")

    @singledispatchmethod
    def check(
        self,
        ann: int | float | str | bool | bytes | type(None) | type | typing._AnyMeta,
        arg: Any,
    ):
        """Check if a value can bind to a type annotation."""
        log.debug(f"Base: {ann=} {arg=}")

        if type(ann) == typing._AnyMeta:
            if self.config.strict:
                raise ValidationError(
                    f"Type {type(ann)} for `{arg}: {ann=}` must be validated, it cannot be left un-annotated! Disable strict validation to allow this."
                )
            else:
                return

        # if newtype we need to check against the base type
        if hasattr(ann, "__supertype__"):
            ann = ann.__supertype__

        if not isinstance(arg, ann):
            raise InvalidType(f"{ann=} can not validate {arg=}")

        self.__check_with_custom_validators(ann, arg)

    @check.register
    def _(
        self,
        ann: types.GenericAlias | typing._GenericAlias | typing._SpecialGenericAlias,
        arg: Any,
    ):
        log.debug(f"GenericAlias: {ann=} {arg=}")

        if hasattr(ann, "__args__") and len(ann.__args__):
            # TODO: These are really hacky...using {} and []...etc.. :(
            if issubclass(ann.__origin__, dict):
                self.check({"arg_types": ann.__args__}, arg)
            elif issubclass(ann.__origin__, list):
                self.check([*ann.__args__], arg)
            elif issubclass(ann.__origin__, tuple):
                self.check(ann.__args__, arg)
            elif issubclass(ann.__origin__, set):
                self.check(set(ann.__args__), arg)

    @check.register
    def _(self, ann: typing.TypeVar, arg: Any):
        """Handle TypeVars"""
        log.debug(
            f"TypeVar: {ann=} {arg=}\n{ann.__constraints__=}, {type(arg)=}, {type(arg) in [c for c in ann.__constraints__]=}"
        )

        if len(ann.__constraints__):
            constraint_types = [type(c) for c in ann.__constraints__]
            if type(arg) in constraint_types:
                # check against constraints
                self.check(type(arg), arg)
            elif type(arg) not in ann.__constraints__:
                raise ValidationError(
                    f"{arg=} is not valid for {ann=} with constraints {ann.__constraints__}"
                )

        if not self.config.ignore_generics:
            self.Gbinds.try_bind_new_arg(ann, arg)

    @check.register
    def _(self, ann: list, arg: Any):
        """Handle generic sequences"""
        log.debug(f"list: {ann=} {arg=}")

        if not isinstance(arg, list):
            raise InvalidType(f"{arg=} is not a list")

        if self.config.no_list_check or self.config.performance:
            return

        # list like list[T] or list[X]
        if len(ann) == 1:
            for a in arg:
                self.check(ann[0], a)

    @check.register
    def _(self, ann: set, arg: Any):
        """Handle generic sets"""
        log.debug(f"set: {ann=} {arg=}")

        if not isinstance(arg, set):
            raise InvalidType(f"{arg=} is not a set")

        if self.config.no_list_check or self.config.performance:
            return

        # set like set[T] or set[X]
        if len(ann) == 1:
            set_type = next(iter(ann))
            for a in arg:
                self.check(set_type, a)

    @check.register
    def _(self, ann: tuple, arg: Any):
        log.debug(f"tuple: {ann=} {arg=}")

        if not isinstance(arg, tuple):
            raise InvalidType(f"{arg=} is not a tuple")

        if self.config.no_tuple_check or self.config.performance:
            return

        if len(ann) == len(arg):
            # each arg in tuple must bind to each ann in tuple
            for a, b in zip(ann, arg):
                self.check(a, b)

    @check.register
    def _(self, ann: dict, arg: Any):
        log.debug(f"dict: {ann=} {arg=}")

        if not isinstance(arg, dict):
            raise InvalidType(f"{arg=} is not a dict")

        if self.config.no_dict_check or self.config.performance:
            return

        if ann["arg_types"] is not None:
            for k, v in arg.items():
                self.check(ann["arg_types"][0], k)
                self.check(ann["arg_types"][1], v)

    @check.register
    def _(self, ann: types.UnionType | typing._UnionGenericAlias, arg: Any):
        """Handle union types"""
        log.debug(f"Union: {ann=} {arg=}")

        for a in ann.__args__:
            try:
                # TODO: This probably will cause a bug as it could bind and then fail, leaving some bound remnants.
                self.check(a, arg)  # , update_bindings=False) # ?
                return
            except ValidationError:
                pass

        raise ValidationError(f"{arg=} failed to bind to {ann=}")

    @check.register
    def _(self, ann: typing._UnpackGenericAlias, arg: Any):
        """Handle unpacked generic types"""
        log.debug(
            f"UnpackGenericAlias: {ann=} {arg=}, {ann.__origin__=} {ann.__args__=}"
        )

        # support for single type like list[int]
        if len(ann.__args__) == 1:
            log.debug(
                f"UnpackGenericAlias: {self.Gbinds} {ann.__args__[0]=} {type(ann.__args__[0])=}, {type(arg)=}"
            )
            self.Gbinds.try_bind_new_arg(ann.__args__[0], arg)
            log.debug(f"UnpackGenericAlias: {self.Gbinds}")

    @check.register
    def _(self, ann: typing.TypeVarTuple, arg: Any):
        """Handle TypeVarTuples"""
        log.debug(f"TypeVarTuple: {ann=} {arg=}")

        if self.config.no_tuple_check or self.config.performance:
            return

        for e in arg:
            self.Gbinds.try_bind_new_arg(ann, e)

    @check.register
    def _(self, ann: typing._TypedDictMeta, arg: Any):
        """Handle TypedDicts"""
        log.debug(f"TypedDictMeta: {ann=} {arg=}")

        if self.config.no_dict_check or self.config.performance:
            return

        for k, v in arg.items():
            self.check(ann.__annotations__[k], v)

    @check.register
    def _(self, ann: typing._LiteralGenericAlias, arg: Any):
        """Handle Literal types"""
        log.debug(f"LiteralGenericAlias: {ann=} {arg=}")

        if arg not in ann.__args__:
            raise ValidationError(f"{arg=} failed to bind to {ann=}")

    @check.register
    def _(self, ann: typing._CallableGenericAlias, arg: Any):
        """Handle Callable types"""
        log.debug(f"CallableGenericAlias: {ann=} {arg=}")

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
