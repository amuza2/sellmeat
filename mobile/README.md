# لحم طازج (Lahem Tazj)

Fresh meat ordering mobile app, built with Flet and MVVM architecture.

## Setup

```bash
uv venv
uv pip install -e .
```

## Run

```bash
# Desktop
flet run main.py

# Web (for testing on mobile via Flet app)
flet run main.py --web

# Android (requires Android SDK)
flet run main.py --android
```

## Build APK

```bash
flet build apk
```

## Architecture

MVVM (Model-View-ViewModel):
- **models/** — Pydantic data classes matching API schemas
- **viewmodels/** — Observable properties + commands (no Flet imports)
- **views/** — Flet UI pages binding to ViewModels
- **services/** — API client with automatic token refresh
- **components/** — Reusable UI components
- **auth.py** — Session management with persistent token storage

