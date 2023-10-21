#!/usr/bin/env python
import inspect
import logging
from functools import wraps
from itertools import chain
from typing import Callable, Sequence, TypeVar
from collections import namedtuple



log = logging.getLogger(__name__)


class ValidationError(TypeError):
    pass

class InvalidType(ValidationError):
    pass

class BindingError(ValidationError):
    pass


_GenericBinding = namedtuple('_GenericBinding', ['ty', 'instances'], defaults=[None, []])
class GenericBinding(_GenericBinding):
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
            Gbinds[ann] = Gbinds[ann]._replace(ty=type(arg))
        elif Gbinds[ann].ty != type(arg):
            raise ValidationError(
                f"Generic {ann} bound to different types: {Gbinds[ann].ty}, but arg is {type(arg)}"
            )
        Gbinds[ann] = Gbinds[ann]._replace(instances=Gbinds[ann].instances + [arg])

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


# --- unittest body ---
import unittest


@validate
def mymod[T](a: T, b: T):
    return a % b


@validate
def mysum[T, W: (int, float)](a: T, b: T) -> W:
    return float(a + b)


@validate
def badmysum[T, W: (int, float)](a: T, b: T) -> W:
    return str(a + b)


@validate
def variadic_func[T, *Ts](a: T, *args: [T]) -> T:
    if isinstance(a, str):
        return f"{a}".join(args)
    return sum(
        args + (a,),
    )


@validate
def default_arg_func[T, U: (int, float)](a: T, b: U = 10) -> U:
    return b


@validate
def nested_generic_func[T, U](a: (T, U), b: [T]) -> dict:
    return {"first": a, "second": b}


has_e = lambda arg: True if "e" in arg else False


@validate
def with_custom_validator(s: has_e):
    return s


class TestValidationFunctions(unittest.TestCase):
    def test_mymod(self):
        self.assertEqual(mymod(10, 3), 10 % 3)
        self.assertEqual(mymod(10.0, 3.0), 10.0 % 3.0)
        with self.assertRaises(ValidationError):
            mymod(10, 3.0)

    def test_mysum(self):
        self.assertEqual(mysum(1, 2), 3.0)
        with self.assertRaises(ValidationError):
            mysum(1, 2.0)
            badmysum(1, 2)

    def test_variadic_func(self):
        self.assertEqual(variadic_func(1, 2, 3, 4), 10)
        self.assertEqual(variadic_func(1.0, 2.0, 3.0), 6.0)
        self.assertEqual(variadic_func("a", "b", "c"), "bac")
        with self.assertRaises(ValidationError):
            variadic_func(1, 2.0)

    def test_default_arg_func(self):
        self.assertEqual(default_arg_func("Hello"), 10)
        self.assertEqual(default_arg_func("Hello", 20), 20)
        with self.assertRaises(ValidationError):
            default_arg_func("Hello", "World")

    def test_nested_generic_func(self):
        self.assertEqual(
            nested_generic_func((1, "a"), [1, 2, 3]),
            {"first": (1, "a"), "second": [1, 2, 3]},
        )
        self.assertEqual(
            nested_generic_func(("a", 1.0), ["a", "b"]),
            {"first": ("a", 1.0), "second": ["a", "b"]},
        )
        with self.assertRaises(ValidationError):
            nested_generic_func((1, "a"), [1, "b"])

    def test_with_custom_validator(self):
        self.assertEqual(with_custom_validator("Hello"), "Hello")
        with self.assertRaises(ValidationError):
            with_custom_validator("World")


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    # log.addHandler(logging.FileHandler("tiny_validate.log"))
    unittest.main()
