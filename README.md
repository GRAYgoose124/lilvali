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
