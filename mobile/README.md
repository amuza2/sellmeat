# SellMeat Mobile App

Flet-based mobile app for ordering meat, built with MVVM architecture.

## Setup

```bash
uv venv
uv pip install -e .

# Run the app
flet run --android main.py
```

## Architecture

MVVM (Model-View-ViewModel):
- **models/** — Pydantic data classes matching API schemas
- **viewmodels/** — Observable properties + commands (no Flet imports)
- **views/** — Flet UI pages binding to ViewModels
