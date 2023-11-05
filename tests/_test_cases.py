import unittest
from typing import List, Union, Optional, Callable, Any, TypedDict, Literal
from lilvali import validate, ValidationError


class TestTypeChecker(unittest.TestCase):
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

        with self.assertRaises(ValidationError):
            func(None)

    # Test with Optional types
    def test_optional_types(self):
        @validate
        def func(a: Optional[int]):
            return a

        self.assertIsNone(func(None))
        self.assertEqual(func(10), 10)
        with self.assertRaises(ValidationError):
            func("test")

    def test_union_types(self):
        @validate
        def func(a: Union[int, str]):
            return a

        self.assertEqual(func(10), 10)
        self.assertEqual(func("test"), "test")
        with self.assertRaises(ValidationError):
            func(3.14)

    def test_callable_types(self):
        @validate
        def func(a: Callable[[int], str]):
            return a(10)

        self.assertEqual(func(lambda x: str(x)), "10")
        with self.assertRaises(ValidationError):
            func(10)

    def test_nested_collections(self):
        @validate
        def func(a: List[List[int]]):
            return a

        self.assertEqual(func([[1, 2], [3, 4]]), [[1, 2], [3, 4]])
        with self.assertRaises(ValidationError):
            func([[1, "2"], [3, 4]])

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

    def test_custom_error_message(self):
        is_even = validate(lambda arg: arg % 2 == 0, error="Not an even number!")

        @validate
        def func(a: is_even):
            return a

        self.assertEqual(func(2), 2)
        with self.assertRaisesRegex(ValidationError, "Not an even number!"):
            func(3)

    def test_variadic_arguments(self):
        @validate
        def func(a: int, *args: int):
            return a + sum(args)

        self.assertEqual(func(1, 2, 3), 6)
        with self.assertRaises(ValidationError):
            func(1, 2, "3")

    def test_async_functions(self):
        @validate
        async def func(a: int) -> int:
            return a

        loop = asyncio.get_event_loop()
        self.assertEqual(loop.run_until_complete(func(10)), 10)
        with self.assertRaises(ValidationError):
            loop.run_until_complete(func("test"))


if __name__ == "__main__":
    unittest.main()
