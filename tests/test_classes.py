import logging, os, unittest
from dataclasses import dataclass, field

from lilvali import validator, validate
from lilvali.errors import *


log = logging.getLogger(__name__)

if os.environ.get("LILVALI_DEBUG", False) == "True":  # pragma: no cover
    logging.basicConfig(
        level=logging.DEBUG, format="%(funcName)s %(name)s:%(lineno)s %(message)s"
    )


@validate
@dataclass
class SomeClass:
    x: int
    y: str = field(default="hello")

    @validator
    def _x(value):
        if value is None or value < 0:
            raise ValidationError

    @validator
    def _y(value) -> bool:
        return value == "hello"


@validate
class NotADC:
    def __init__(self, x: int, y: str):
        self.x = x
        self.y = y

    @validator
    def _x(value):
        if value is None or value < 0:
            raise ValidationError

    @validator
    def _y(value) -> bool:
        if value != "hello":
            raise ValidationError


class TestValidateTypes(unittest.TestCase):
    def test_dataclass(self):
        self.assertEqual(SomeClass(1, "hello").x, 1)
        self.assertEqual(SomeClass(1).y, "hello")
        with self.assertRaises(ValidationError):
            SomeClass(-1.3, "hello")
        with self.assertRaises(ValidationError):
            SomeClass(1, None)
        with self.assertRaises(ValidationError):
            SomeClass(1.0, "hello")
        with self.assertRaises(ValidationError):
            SomeClass(-1, "hello")
        with self.assertRaises(ValidationError):
            SomeClass(1, "herro")

    def test_not_dataclass(self):
        self.assertEqual(NotADC(1, "hello").x, 1)


def main():
    import pdb

    pdb.set_trace()
    SomeClass(1, "hello")


if __name__ == "__main__":
    main()
