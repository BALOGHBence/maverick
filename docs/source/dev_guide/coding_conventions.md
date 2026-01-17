# Coding Conventions

## Code Formatting with Black

This project uses [black](https://github.com/psf/black) as the code formatter to ensure consistent code style.

**Formatting your code:**

```bash
# Format all Python files in the project
uv run black .

# Format a specific file
uv run black path/to/file.py

# Check what would be formatted without making changes
uv run black --check .

# Show diff of what would change
uv run black --diff .
```

**Black configuration:**

Black uses sensible defaults. The line length is 88 characters by default. If you need to customize black's behavior, you can add settings to `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ['py312']
```
