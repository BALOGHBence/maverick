# Installation for Developers

## Installing uv

If you don't have uv installed, you can install it using one of the following methods:

```bash
# Using pip
pip install uv

# Using curl (Unix-like systems)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Using PowerShell (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Installing the Project

### Clone the repository

```bash
git clone https://github.com/BALOGHBence/maverick.git
cd maverick
```

### Install the project with uv

```bash
# Install the project and its dependencies
uv sync

# Or install in editable mode for development
uv pip install -e .
```

## Installing Development Dependencies

Development dependencies (including Sphinx for documentation and black for code formatting) are managed in the `dev` dependency group:

```bash
# Install with dev dependencies
uv sync --group dev
```
