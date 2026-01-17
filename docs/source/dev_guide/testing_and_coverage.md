# Testing and Coverage

## Running Tests

This project uses `pytest` as the test runner (tests are written using `unittest`).

```bash
# Install dev dependencies (includes pytest)
uv sync --group dev

# Run tests
uv run pytest
```

## Code Coverage

This project uses `pytest-cov` to measure code coverage. Coverage reports help identify which parts of the code are tested and which need more testing.

**Running tests with coverage:**

```bash
# Generate HTML coverage report
uv run pytest --cov-report=html --cov-config=.coveragerc --cov=maverick

# View the coverage report by opening htmlcov/index.html in a browser
```

**Other coverage report formats:**

```bash
# Terminal output with missing lines
uv run pytest --cov-report=term-missing --cov-config=.coveragerc --cov=maverick

# Generate XML report (useful for CI/CD)
uv run pytest --cov-report=xml --cov-config=.coveragerc --cov=maverick

# Combine multiple formats
uv run pytest --cov-report=html --cov-report=term-missing --cov-config=.coveragerc --cov=maverick
```

**Coverage configuration:**

The `.coveragerc` file in the project root contains coverage settings including:

- Source paths and packages to measure
- Branch coverage (tracks both True/False branches in conditionals)
- Files and patterns to exclude from coverage
- HTML report customization
