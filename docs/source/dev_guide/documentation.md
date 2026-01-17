# Documenting

## Building Documentation

The project uses Sphinx for documentation. Documentation source files are in `docs/source/` and built files go to `docs/build/`.

**Building the documentation:**

```bash
# Navigate to the docs directory
cd docs

# Build HTML documentation
uv run sphinx-build -b html source build

# Or use make (if available)
make html

# View the documentation by opening docs/build/index.html in a browser
```
