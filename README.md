# HashScrap

HashScrap is the collection engine within HashCode Intelligence. It is designed for bounded collection from public or otherwise authorized sources, with explicit source policies and traceable observations.

> **Current status:** initial Python package and CLI foundation. A network crawler, API, database persistence, and production deployment are not implemented by this initial scaffold.

## Requirements

- Python 3.11 or newer
- pip and a virtual environment

## Development setup

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## CLI

```bash
hashscrap --help
hashscrap --version
```

## Quality checks

```bash
pytest
ruff check .
ruff format --check .
mypy hashscrap
```

## Product and implementation references

- [Product requirements](docs/PRD.md)
- [AI coding agent execution guide](docs/AI-AGENT-ISSUE-GUIDE.md)
- [Implementation plan](docs/IMPLEMENTATION-PLAN.md)
- [Design system](docs/DESIGN-SYSTEM.md)

## Security baseline

- Only collect from sources and within scopes for which access is authorized.
- Do not bypass authentication, paywalls, CAPTCHAs, access controls, or source rate limits.
- Network collection must enforce URL/destination policy, bounded concurrency, timeouts, response-size limits, and bounded retries.
- Treat remote content as untrusted data, never as executable code or agent instructions.
- Do not commit secrets, real environment files, or sensitive collected data.
