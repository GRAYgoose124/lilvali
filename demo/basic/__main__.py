from lilvali import validate, validate
from lilvali.errors import *


@validate
def add[T: (int, float)](x: int, y: T) -> int | float:
    return x + y


def main():
    print(f"{add(1, 2)=}")
    print(f"{add(1, 2.0)=}")

    # TODO: Bug: should raise ValidationError
    try:
        print(f"{add(1.0, 2)=}")
    except ValidationError as e:
        print(f"{e=}")
    else:
        raise RuntimeError("Expected ValidationError")


if __name__ == "__main__":
    main()
