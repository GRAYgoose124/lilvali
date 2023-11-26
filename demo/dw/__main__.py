import inspect
import json, os, logging
from dataclasses import dataclass
from dataclass_wizard import JSONWizard
import dataclass_wizard

from lilvali import validate, validator
from lilvali.errors import *


log = logging.getLogger(__name__)
if os.environ.get("LILVALI_DEBUG", False) == "True":  # pragma: no cover
    logging.basicConfig(level=logging.DEBUG, format="%(name)s:%(lineno)s %(message)s")


def damn(decorator):
    def decorate(cls):
        for attr_name, attr_value in cls.__dict__.items():
            if not attr_name.startswith("_") and callable(func := attr_value):
                log.debug(f"decorating {attr_name} with {decorator}")
                func.validated_base_cls = cls
                setattr(cls, attr_name, decorator(func))
        return cls

    return decorate


def test_validate():
    @validate
    def add[T: (int, float)](x: int, y: T) -> int | float:
        return x + y

    print(f"{add(1, 2)=}")
    print(f"{add(1, 2.0)=}")

    try:
        print(f"{add(1.0, 2)=}")
    except ValidationError as e:
        pass


def test_validated_cls():
    total_validate = lambda cls: damn(validate)(validate(cls))

    @total_validate
    @dataclass
    class SomeSchema(JSONWizard):
        """a dataclass that defines a json schema."""

        name: str
        data: dict[str, int]

        @classmethod
        def from_dict(cls, value: dict):
            return super().from_dict(value)

    c = SomeSchema.from_dict({"name": "A", "data": {}})
    print(c)

    try:
        SomeSchema.from_dict("not_a_dict")
    except ValidationError:
        print("GOTCHA!")
    except dataclass_wizard.errors.MissingFields:
        print("DARN IT WE LOST 'ER!")

    try:
        SomeSchema(1, False)
    except ValidationError:
        print("GOOD STUFF!")


def main():
    test_validate()
    test_validated_cls()


if __name__ == "__main__":
    main()
