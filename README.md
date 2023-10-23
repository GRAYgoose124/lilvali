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


## TODO
- maybe: 
  - cache validated args with their bindings?
  - recursive validation
  - register custom validators at runtime 
- support typing: TypeAlias, NewType, Literal, Any, etc.