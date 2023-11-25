import logging, os, inspect, unittest
from dataclasses import dataclass, fields, field
from functools import wraps

from lilvali import validator, ValidationError, ValidatorMeta


log = logging.getLogger(__name__)

if os.environ.get("LILVALI_DEBUG", False) == "True":  # pragma: no cover
    logging.basicConfig(
        level=logging.DEBUG, format="%(funcName)s %(name)s:%(lineno)s %(message)s"
    )


class SomeClass(metaclass=ValidatorMeta):
    x: int
    y: str = field(default="hello")

    @validator
    def _x(value) -> bool:
        return value is not None and value > 0

    @validator
    def _y(value) -> bool:
        return value == "hello"


class TestValidateTypes(unittest.TestCase):
    def test_model(self):
        self.assertEqual(SomeClass(1, "hello").x, 1)
        self.assertEqual(SomeClass(1).y, "hello")
        with self.assertRaises(ValidationError):
            SomeClass(-1.3, "hello")
        # with self.assertRaises(ValidationError):
        #     SomeClass(1, "herro")
        with self.assertRaises(ValidationError):
            SomeClass(1, None)
        with self.assertRaises(ValidationError):
            SomeClass(1.0, "hello")


def main():
    import pdb

    pdb.set_trace()
    SomeClass(1, "hello")


if __name__ == "__main__":
    main()
