import logging
import os
import unittest

from lilvali.validate import validate, validator, ValidationError


class TestValidationFunctions(unittest.TestCase):
    # setup
    def setUp(self) -> None:
        if os.getenv("LILVALI_DEBUG", "False") == "True":
            logging.basicConfig(
                level=logging.DEBUG, format="%(levelname)s: %(message)s"
            )
            logging.getLogger("validate").addHandler(
                logging.FileHandler("lilvali_unittest_debug.log")
            )
        return super().setUp()

    def test_mymod(self):
        @validate
        def mymod[T](a: T, b: T):
            return a % b

        self.assertEqual(mymod(10, 3), 10 % 3)
        self.assertEqual(mymod(10.0, 3.0), 10.0 % 3.0)
        with self.assertRaises(ValidationError):
            mymod(10, 3.0)

    def test_mysum(self):
        @validate
        def mysum[T, W: (int, float)](a: T, b: T) -> W:
            return float(a + b)

        @validate
        def badmysum[T, W: (int, float)](a: T, b: T) -> W:
            return str(a + b)

        self.assertEqual(mysum(1, 2), 3.0)
        with self.assertRaises(ValidationError):
            mysum(1, 2.0)
            badmysum(1, 2)

    def test_variadic_func(self):
        @validate
        def variadic_func[T, *Ts](a: T, *args: [T]) -> T:
            if isinstance(a, str):
                return f"{a}".join(args)
            return sum(
                args + (a,),
            )

        self.assertEqual(variadic_func(1, 2, 3, 4), 10)
        self.assertEqual(variadic_func(1.0, 2.0, 3.0), 6.0)
        self.assertEqual(variadic_func("a", "b", "c"), "bac")
        with self.assertRaises(ValidationError):
            variadic_func(1, 2.0)

    def test_default_arg_func(self):
        @validate
        def default_arg_func[T, U: (int, float)](a: T, b: U = 10) -> U:
            return b

        self.assertEqual(default_arg_func("Hello"), 10)
        self.assertEqual(default_arg_func("Hello", 20), 20)
        with self.assertRaises(ValidationError):
            default_arg_func("Hello", "World")

    def test_generic_sequence_func(self):
        @validate
        def generic_sequence_func[T, U](a: (T, U), b: [T]) -> dict:
            return {"first": a, "second": b}

        self.assertEqual(
            generic_sequence_func((1, "a"), [1, 2, 3]),
            {"first": (1, "a"), "second": [1, 2, 3]},
        )
        self.assertEqual(
            generic_sequence_func(("a", 1.0), ["a", "b"]),
            {"first": ("a", 1.0), "second": ["a", "b"]},
        )
        with self.assertRaises(ValidationError):
            generic_sequence_func((1, "a"), [1, "b"])

        @validate
        def generic_tuple_return[T, U: (int, float)](a: T, b: U) -> (T, U):
            return a, b

        self.assertEqual(generic_tuple_return(1, 2), (1, 2))
        self.assertEqual(generic_tuple_return(1, 2.0), (1, 2.0))
        with self.assertRaises(ValidationError):
            generic_tuple_return(1, "a")

    def test_with_custom_validator(self):
        has_e = validator(lambda arg: True if "e" in arg else False)
        @validate
        def with_custom_validator(s: has_e):
            return s
        
        self.assertEqual(with_custom_validator("Hello"), "Hello")
        with self.assertRaises(ValidationError):
            with_custom_validator("World")

        @validator(base=int)
        def has_c_or_int(arg): 
            return True if "c" in arg else False
        #has_c_or_int = validator(lambda arg: True if "c" in arg else False, base=int)

        @validate
        def with_custom_validator2(s: has_c_or_int):
            return s

        self.assertEqual(with_custom_validator2(10), 10)
        self.assertEqual(with_custom_validator2("has_c"), "has_c")
        with self.assertRaises(ValidationError):
            self.assertEqual(with_custom_validator2("Hello"), "Hello")

    def test_generic_union(self):
        @validate
        def generic_union[T: (str, bool)](a: int | T) -> int | T:
            return a
        
        self.assertEqual(generic_union(10), 10)
        self.assertEqual(generic_union("Hello"), "Hello")
        with self.assertRaises(ValidationError):
            generic_union(10.0)

    def test_generic_union_with_constraints(self):
        @validate
        def add[T: (int, float)](x: int, y: T) -> int | float:
            return x + y
        
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(1, 2.0), 3.0)
        with self.assertRaises(ValidationError):
            add(1.0, 2)

    def test_validate_dict(self):
        @validate
        def func_a(a: dict):
            return ";".join(f"{k},{v}" for k,v in a.items())

        @validate
        def func_b(a: dict[str, int]) -> int:
            return sum(a.values())
        
        self.assertEqual(func_a({'a': 1, 'b': 2}),  "a,1;b,2")
        self.assertEqual(func_b({'a': 1, 'b': 2}), 3)
        with self.assertRaises(ValidationError):
            func_b({'a': 1, 'b': 'c'})



if __name__ == "__main__":
    unittest.main()
