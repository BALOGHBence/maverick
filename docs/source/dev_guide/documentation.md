# Documenting

The documentation for the project is generated using Sphinx. Writing documentation consists of the following components:

- Writing docstrings for classes and functions as you write code.
- Adding documentation for the Sphinx-generated documentation on top of what the docstrings provide.

## Writing Docstrings

Every user facing class and function should have a docstring written in NumPy-style, according to the [NumPyDoc conventions](https://numpydoc.readthedocs.io/en/latest/format.html). A good ocstring

- Has a short first line, summarizing what the class or method does.
- Has more detailed description if the complexity of the class or method requires.
- List all parameters with their explanation.
- Has a 'Returns' section if the returned type is not trivial.
- Has a 'Raises' section if the method raises exceptions.
- Has an 'Examples' section with one or more code snippets if the complexity of the class or method requires. The code snippets should be self-contained in terms of import statements.

## Writing Source Files for Sphinx

```{note}
This section is under construction.
```

## Building the Documentation

The project uses Sphinx for documentation. Documentation source files are in `docs/source/` and built files go to `docs/build/`.

**Building the documentation:**

```bash
# Navigate to the docs directory
cd docs

# Build HTML documentation
uv run sphinx-build -b html source build

# Or use make (if available)
uv run make html

# View the documentation by opening docs/build/index.html in a browser
```
