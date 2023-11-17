# lilVali

A small Python 3.12 validation experiment for playing with [PEP 695](https://peps.python.org/pep-0695/). 

> Supports most basic typing constructs including Generics.

## Install
```bash
pip install lilvali
```

## Basic Usage
```python
from lilvali import validate, validator, ValidationError


@validate
def add[T: (int, float)](x: int, y: T) -> int | float:
    return x + y


def main():
    print(f"{add(1, 2)=}")
    print(f"{add(1, 2.0)=}")

    try:
        print(f"{add(1.0, 2)=}")
    except ValidationError as e:
        print(f"{e=}")
    else:
        raise RuntimeError("Expected ValidationError")


if __name__ == "__main__":
    main()
```


## Usage
After installing:
```bash
# (Does nothing right now.)
lilvali
```

```python
from lilvali import validate, validator, ValidationError
```

## Tests
```bash
Running tests with coverage
.........................
----------------------------------------------------------------------
Ran 25 tests in 0.006s

OK
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
lilvali/__init__.py                2      0   100%
lilvali/binding.py               167      0   100%
lilvali/errors.py                  6      0   100%
lilvali/validate.py               80      0   100%
tests/test_tiny_validate.py      195      0   100%
tests/test_validate_types.py     124      0   100%
------------------------------------------------------------
TOTAL                            574      0   100%
```

[TODO](docs/TODO.md)