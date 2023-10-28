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
./tests/tests.sh
```

```bash
Running tests with coverage
.....................
------------------------------------------------------------
Ran 21 tests in 0.003s

OK
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
lilvali/__init__.py                2      0   100%
lilvali/binding.py               113      6    95%   69, 77, 132, 157, 190-191
lilvali/errors.py                  6      0   100%
lilvali/validate.py               70      0   100%
tests/test_tiny_validate.py      147      7    95%   26, 31, 146, 184, 195, 204, 212
tests/test_validate_types.py      78      0   100%
------------------------------------------------------------
TOTAL                            416     13    97%
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
