import logging, os, inspect, unittest
from dataclasses import dataclass, fields, field
from functools import wraps

from lilvali import (
    validate,
    validator,
    VM,
    ValidationError,
    ValidatorFunction,
    ValidatorMeta
)


log = logging.getLogger(__name__)


class SomeClass(metaclass=ValidatorMeta):
    x: int = field(default=0)
    y: str = field(default="")

    @validator
    @staticmethod
    def _X(value) -> bool:
        print("CHECK")
        return value is not None and value > 0

    @validator
    @staticmethod
    def _y(value) -> bool:
        print("CHECK")
        return value == "hello"


# Test code remains the same


class TestValidateTypes(unittest.TestCase):
    def setUp(self):
        if os.environ.get("LILVALI_DEBUG", False) == "True":  # pragma: no cover
            logging.basicConfig(
                level=logging.DEBUG, format="%(name)s:%(lineno)s %(message)s"
            )

        super().setUp()

    def test_model(self):
        log.debug(f"X{SomeClass(1, "hello")}")
        # self.assertEqual(SomeClass(1, "hello").x, 1)
        with self.assertRaises(ValidationError):
            SomeClass(-1.3, "hello")
        # with self.assertRaises(ValidationError):
        #     SomeClass(1, "herro")
        # with self.assertRaises(ValidationError):
        #     SomeClass(1, None)

        # TODO: fix this, should fail, not using validate stack is why it isn't.
        # with self.assertRaises(ValidationError):
        #     SomeClass(1.0, "hello")
