# Documenting

The documentation for the project is generated using Sphinx. Writing documentation consists of the following components:

- Writing docstrings for classes and functions as you write code.
- Adding documentation for the Sphinx-generated documentation on top of what the docstrings provide.

## Writing Docstrings

Every user facing class and function should have a docstring written in NumPy-style, according to the [NumPyDoc conventions](https://numpydoc.readthedocs.io/en/latest/format.html). A good docstring

- Has a short first line, summarizing what the class or method does.
- Has more detailed description if the complexity of the class or method requires.
- List all parameters with their explanation.
- Has a 'Returns' section if the returned type is not trivial.
- Has a 'Raises' section if the method raises exceptions.
- Has an 'Examples' section with one or more code snippets if the complexity of the class or method requires. The code snippets should be self-contained in terms of import statements.

## Writing Source Files for Sphinx

Documentation source files live in `docs/source/`. The project supports three file types:

| Extension | Format | When to use |
| --- | --- | --- |
| `.md` | MyST Markdown | All narrative pages, user guide, examples |
| `.ipynb` | Jupyter notebook | Interactive examples with code output |
| `.rst` | reStructuredText | `index.rst` TOC files only |

### Adding a new page

1. Create the file in the appropriate subdirectory of `docs/source/`.
2. Add the filename (without extension) to the `toctree` in the nearest `index.rst`.

### MyST directives used in this project

**Admonitions:**

````markdown
```{note}
This is a note.
```

```{warning}
This is a warning.
```
````

**Cross-references between pages** (path relative to `docs/source/`, no extension):

```markdown
See {doc}`Documenting <dev_guide/documentation>` for details.
```

**Cross-references to API symbols:**

```markdown
{class}`maverick.Game`
{meth}`~maverick.Game.start`   ← ~ shows only the short name
{func}`maverick.utils.score_hand`
```

**Code blocks:**

````markdown
```python
from maverick import Game
```
````

**Literal file include** (path relative to the source file):

````markdown
```{literalinclude} ../../path/to/file.py
:language: python
```
````

**Raw HTML** (used for download buttons):

````markdown
```{raw} html
<a href="...">Download</a>
```
````

(building-the-documentation)=
## Building the Documentation

### Install documentation dependencies

The Sphinx toolchain is in the `docs` dependency group. Install it before building:

```bash
uv sync --group docs
```

### Build the HTML documentation

Run the following command from the **project root**:

```bash
uv run sphinx-build docs/source docs/build/html
```

Or use `make` from the `docs/` directory:

```bash
cd docs
uv run make html
```

The built output is written to `docs/build/html/`. Open `docs/build/html/index.html` in a browser to preview it.
