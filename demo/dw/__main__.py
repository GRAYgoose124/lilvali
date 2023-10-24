import json 
from dataclasses import dataclass
from dataclass_wizard import JSONWizard, JSONSerializable

from lilvali import validate, validator, ValidationError


def damn(decorator):
    def decorate(cls):
        for attr_name, attr_value in cls.__dict__.items():
            if callable(attr_value):
                setattr(cls, attr_name, decorator(attr_value))
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
        print(f"{e=}")
    else:
        raise RuntimeError("Expected ValidationError")


def test_validated_cls():
    @damn(validate)
    @dataclass
    class SomeSchema(JSONWizard):
        """ a dataclass that defines a json schema. """
        name: str
        data: dict[str, int]


    c = SomeSchema.from_dict({"name": "A", "data": {}})
    print(c)


def main():
    test_validate()
    test_validated_cls()

if __name__ == "__main__":
    main()
