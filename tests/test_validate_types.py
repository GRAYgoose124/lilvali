import logging
import os
import unittest
from typing import Optional, Literal, TypedDict, Union, Any, Callable

from lilvali.validate import validate, validator, ValidationError


class TestValidateTypes(unittest.TestCase):
    def test_optional(self):
        @validate
        def optional_func(a: Optional[int]) -> int:
            return a or 0

        self.assertEqual(optional_func(None), 0)
        self.assertEqual(optional_func(5), 5)
        with self.assertRaises(ValidationError):
            optional_func("Hello")

    def test_literal(self):
        @validate
        def literal_func(a: Literal["Yes", "No"]) -> str:
            return a

        self.assertEqual(literal_func("Yes"), "Yes")
        self.assertEqual(literal_func("No"), "No")
        with self.assertRaises(ValidationError):
            literal_func("Maybe")

    def test_typed_dict(self):
        class Person(TypedDict):
            name: str
            age: int

        @validate
        def person_func(p: Person) -> str:
            return p["name"]

        self.assertEqual(person_func({"name": "Alice", "age": 30}), "Alice")
        with self.assertRaises(ValidationError):
            person_func({"name": "Alice", "age": "Unknown"})

    def test_union(self):
        @validate
        def union_func(a: Union[int, str, float]) -> str:
            return str(a)

        self.assertEqual(union_func(5), "5")
        self.assertEqual(union_func("Hello"), "Hello")
        self.assertEqual(union_func(5.5), "5.5")
        with self.assertRaises(ValidationError):
            union_func([])

        @validate
        def union_func2(a: str | int | float) -> str:
            return str(a)

        self.assertEqual(union_func2(5), "5")
        self.assertEqual(union_func2("Hello"), "Hello")
        self.assertEqual(union_func2(5.5), "5.5")
        with self.assertRaises(ValidationError):
            union_func2([])

    def test_any(self):
        @validate(config={"strict": False})
        def any_func(a: Any) -> str:
            return str(a)

        self.assertEqual(any_func(5), "5")
        self.assertEqual(any_func("Hello"), "Hello")
        self.assertEqual(any_func([1, 2, 3]), "[1, 2, 3]")

        @validate
        def any_func2(a: Any) -> str:
            return str(a)

        with self.assertRaises(ValidationError):
            any_func2(5)

        any_func2.checking_off()
        self.assertEqual(any_func2(5), "5")

    def test_callable(self):
        @validate
        def callable_func(a: Callable[[int], str]) -> str:
            return a(5)

        def the_callable(x: int) -> str:
            return str(x)

        self.assertEqual(callable_func(the_callable), "5")

        with self.assertRaises(ValidationError):
            callable_func(lambda x: str(x))

        with self.assertRaises(ValidationError):
            callable_func("Not a function")

        @validate(config={"implied_lambdas": True})
        def callable_func2(a: Callable[[int], str]) -> str:
            return a(5)

        self.assertEqual(callable_func2(lambda x: str(x)), "5")

    def test_type(self):
        @validate
        def type_func(a: type) -> bool:
            return isinstance(a, type)

        self.assertTrue(type_func(int))
        with self.assertRaises(ValidationError):
            type_func("Not a type")
