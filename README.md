# lilVali

A small Python 3.12 validation experiment for playing with [PEP 695](https://peps.python.org/pep-0695/).

## Install
The following commands are assuming you've just cloned the repo and haven't `cd`'d yet. Otherwise, replace `lilvali` with `.`

### Requirements
Currently optional except for `demo/dw`.
```bash
pip install -r lilvali/requirements.txt
```

### Installing
```bash
# For development:
pip install -e lilvali

# otherwise:
pip install lilvali
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
python lilvali/demo/basic

python lilvali/demo/dw # reqires dataclass_wizard
```

### Testing
```bash
LILVALI_DEBUG="False" python -m unittest discover -s lilvali/tests 
```
```py
#### Coverage
Name                           Stmts   Miss  Cover
--------------------------------------------------
lilvali/__init__.py                2      0   100%
lilvali/binding.py               113      6    95%
lilvali/errors.py                  6      0   100%
lilvali/validate.py               72      3    96%
tests/test_tiny_validate.py      144      7    95%
tests/test_validate_types.py      78      0   100%
--------------------------------------------------
TOTAL                            415     16    96%
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
