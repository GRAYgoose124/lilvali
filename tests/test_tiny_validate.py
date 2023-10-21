import unittest

from lilvali.validate import validate, ValidationError

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
