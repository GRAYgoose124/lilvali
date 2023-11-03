# lilVali

A small Python 3.12 validation experiment for playing with [PEP 695](https://peps.python.org/pep-0695/).

## Install
```bash
cd lilvali
```

### Requirements
Currently optional except for `demo/dw`.
```bash
pip install -r requirements.txt
```

### Installing
```bash
# For development:
pip install -e .

# otherwise:
pip install .
```


## Usage
After installing:
```bash
# (Does nothing right now.)
lilvali
```
### Demos
```bash
# You may also want to try the demo:
python demo/basic

python demo/dw # reqires dataclass_wizard
```

### Testing
```bash
LILVALI_DEBUG=True ./tests/tests.sh
```

```bash
Running tests with coverage
.....................
------------------------------------------------------------
Ran 21 tests in 0.004s

OK
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
lilvali/__init__.py                2      0   100%
lilvali/binding.py               111      0   100%
lilvali/errors.py                  6      0   100%
lilvali/validate.py               69      0   100%
tests/test_tiny_validate.py      154      0   100%
tests/test_validate_types.py      85      0   100%
------------------------------------------------------------
TOTAL                            427      0   100%
```

## TODO
- [x] Generic/TypeVar support
- [x] partial support for typing module
### maybe
  - [x] cache validated args with their bindings
    - already done, but this may not be necessary for *this* project.
  - [/] recursive validation
    - [x] dict k/v validation
    - [ ] dataclass/JsonWizard support
