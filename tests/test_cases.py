import logging, os, unittest
from typing import List, Union, Optional, Callable, Any, TypedDict, Literal

from lilvali import validate
from lilvali.errors import *


class TestValidateTypes(unittest.TestCase):
    def setUp(self):
        if os.environ.get("LILVALI_DEBUG", False) == "True":  # pragma: no cover
            logging.basicConfig(
                level=logging.DEBUG, format="%(name)s:%(lineno)s %(message)s"
            )

        super().setUp()

    def test_type(self):
        @validate
        def type_func(a: type) -> bool:
            return isinstance(a, type)

        self.assertTrue(type_func(int))
        with self.assertRaises(ValidationError):
            type_func("Not a type")

    def test_basic_types(self):
        @validate
        def func(a: int, b: str, c: float, d: bool):
            return f"{a}, {b}, {c}, {d}"

        self.assertEqual(func(1, "test", 3.14, True), "1, test, 3.14, True")
        with self.assertRaises(ValidationError):
            func("1", "test", 3.14, True)

    def test_none_not_allowed(self):
        @validate
        def func(a: int):
            return a

        self.assertEqual(func(10), 10)
        with self.assertRaises(ValidationError):
            func(None)

    def test_none_allowed(self):
        @validate
        def func(a: Optional[int]):
            return a

        self.assertIsNone(func(None))
        self.assertEqual(func(10), 10)
        with self.assertRaises(ValidationError):
            func("test")

    def test_optional_types(self):
        @validate
        def func(a: Optional[int]):
            return a

        self.assertIsNone(func(None))
        self.assertEqual(func(10), 10)
        with self.assertRaises(ValidationError):
            func("test")

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
            union_func2(set([1]))
        with self.assertRaises(ValidationError):
            union_func2([])
        with self.assertRaises(ValidationError):
            union_func2({})

    def test_union_types(self):
        @validate
        def func(a: Union[int, str]):
            return a

        self.assertEqual(func(10), 10)
        self.assertEqual(func("test"), "test")
        with self.assertRaises(ValidationError):
            func(3.14)

    def test_callable_types(self):
        @validate(config={"implied_lambdas": True})
        def func(a: Callable[[int], str]):
            return a(10)

        def func2(a: int) -> str:
            return str(a)

        self.assertEqual(func(func2), "10")
        self.assertEqual(func(lambda x: str(x)), "10")
        with self.assertRaises(ValidationError):
            func(10)

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

    def test_nested_collections(self):
        @validate
        def func(a: List[List[int]]):
            return a

        self.assertEqual(func([[1, 2], [3, 4]]), [[1, 2], [3, 4]])
        with self.assertRaises(ValidationError):
            func([[1, "2"], [3, 4]])

    def test_set(self):
        @validate
        def set_func(a: set[int]) -> str:
            return str(a)

        self.assertEqual(set_func({1, 2, 3}), "{1, 2, 3}")
        with self.assertRaises(ValidationError):
            set_func({1, "a", 3})

        with self.assertRaises(ValidationError):
            set_func([1, 2, 3])

        @validate(config={"performance": True})
        def set_func2(a: set[int]) -> str:
            return str(a)

        self.assertEqual(set_func2({1, 2, 3}), "{1, 2, 3}")

    def test_typed_dict(self):
        class Person(TypedDict):
            name: str
            age: int

        @validate
        def func(p: Person):
            return p["name"]

        self.assertEqual(func({"name": "Alice", "age": 30}), "Alice")
        with self.assertRaises(ValidationError):
            func({"name": "Alice", "age": "Unknown"})

    def test_literal_types(self):
        @validate
        def func(a: Literal["Yes", "No"]):
            return a

        self.assertEqual(func("Yes"), "Yes")
        self.assertEqual(func("No"), "No")
        with self.assertRaises(ValidationError):
            func("Maybe")

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

    # def test_async_functions(self):
    #     @validate
    #     async def func(a: int) -> int:
    #         return a

    #     loop = asyncio.get_event_loop()
    #     self.assertEqual(loop.run_until_complete(func(10)), 10)
    #     with self.assertRaises(ValidationError):
    #         loop.run_until_complete(func("test"))
