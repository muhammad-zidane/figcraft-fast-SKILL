# Contributing to `figcraft-fast-SKILL`

Thank you for contributing to `figcraft-fast-SKILL`.

## Development Setup

1. Requires **Python 3.10+** (standard library only; no external dependencies).
2. Create a feature branch from `master`:
   ```bash
   git checkout -b feat/your-change
   ```

## Quality & Testing Requirements

Before opening a Pull Request, ensure all unit tests and bytecode checks pass:

```bash
python -m unittest discover -s scripts -p "test_*.py" -v
python -m py_compile scripts/*.py examples/*.py
```

## Repository Hygiene

- Do **not** commit machine-specific absolute paths (e.g., local user directories).
- Do **not** commit backup files (`*.bak`), cache directories (`__pycache__/`), or generated binary `.figcraft` artifacts.
- Keep `SKILL.md` and `README.md` synchronized when changing `FigCraftClient` defaults or public APIs.
