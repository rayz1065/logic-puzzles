# Logical Puzzles
A simple collection of logical puzzles and solvers.

## Setup environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Remember to then update the interpreter in your editor.

## Automatically update PYTHONPATH

Add this in .venv/bin/activate:
```bash
export PYTHONPATH="${PYTHONPATH}:${VIRTUAL_ENV}/../"
```
