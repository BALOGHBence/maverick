# Maverick

A Python project using uv package manager with src layout.

[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/benceeokf)

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installing uv

If you don't have uv installed, you can install it using one of the following methods:

```bash
# Using pip
pip install uv

# Using curl (Unix-like systems)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Using PowerShell (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installing the Project

1. Clone the repository:
```bash
git clone https://github.com/BALOGHBence/maverick.git
cd maverick
```

2. Install the project with uv:
```bash
# Install the project and its dependencies
uv sync

# Or install in editable mode for development
uv pip install -e .
```

## Usage

### Running the Application

Once installed, you can run the application using:

```bash
uv run maverick
```

Or if you installed it in your environment:

```bash
maverick
```

### Step-by-Step Game Execution

The Game class supports two execution modes:

#### 1. Standard Execution (run entire game)

```python
from maverick import Game
from maverick.players import CallBot
from maverick.playerstate import PlayerState

game = Game(small_blind=10, big_blind=20, max_hands=1)
game.add_player(CallBot(id="p1", name="Alice", state=PlayerState(stack=100, seat=0)))
game.add_player(CallBot(id="p2", name="Bob", state=PlayerState(stack=100, seat=1)))

# Run the entire game at once
game.start()
```

#### 2. Step-by-Step Execution (process events one at a time)

```python
from maverick import Game
from maverick.players import CallBot
from maverick.playerstate import PlayerState
from maverick.enums import GameEventType

game = Game(small_blind=10, big_blind=20, max_hands=1)
game.add_player(CallBot(id="p1", name="Alice", state=PlayerState(stack=100, seat=0)))
game.add_player(CallBot(id="p2", name="Bob", state=PlayerState(stack=100, seat=1)))

# Initialize and start manually
game._initialize_game()
game._event_queue.append(GameEventType.GAME_STARTED)

# Process events one at a time
while game.has_events():
    game.step()
    # Do something between events (logging, analysis, etc.)
    print(f"Current state: {game.state.state_type}")
```

**Available methods:**
- `step()` - Process a single event from the queue, returns `True` if an event was processed
- `has_events()` - Check if there are pending events in the queue

See `sandbox/demo_step_execution.py` for a complete working example.

### Development

#### Installing Development Dependencies

Development dependencies (including Sphinx for documentation and black for code formatting) are managed in the `dev` dependency group:

```bash
# Install with dev dependencies
uv sync --group dev
```

#### Code Formatting with Black

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

#### Building Documentation

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

#### Running Tests

This project uses `pytest` as the test runner (tests are written using `unittest`).

```bash
# Install dev dependencies (includes pytest)
uv sync --group dev

# Run tests
uv run pytest
```

#### Code Coverage

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

## Basic Git Commands

Here are some essential Git commands for working with this repository:

### Initial Setup

```bash
# Configure your Git identity (first time only)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Clone the repository
git clone https://github.com/BALOGHBence/maverick.git
cd maverick
```

### Daily Workflow

```bash
# Check the status of your working directory
git status

# View changes you've made
git diff

# Stage changes for commit
git add .                    # Add all changes
git add path/to/file.py      # Add specific file

# Commit your changes
git commit -m "Description of changes"

# Push changes to remote repository
git push origin main

# Pull latest changes from remote
git pull origin main
```

### Branching

```bash
# Create a new branch
git branch feature-name

# Switch to a branch
git checkout feature-name

# Create and switch to a new branch in one command
git checkout -b feature-name

# List all branches
git branch -a

# Merge a branch into current branch
git merge feature-name

# Delete a branch
git branch -d feature-name
```

### Viewing History

```bash
# View commit history
git log

# View condensed history
git log --oneline

# View changes in a specific commit
git show <commit-hash>
```

### Undoing Changes

```bash
# Discard changes in working directory
git checkout -- path/to/file.py

# Unstage a file (keep changes)
git reset HEAD path/to/file.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes - careful!)
git reset --hard HEAD~1
```

## Project Structure

```
maverick/
├── src/
│   └── maverick/          # Main package source code
│       └── __init__.py
├── docs/
│   ├── source/            # Sphinx documentation source
│   │   ├── conf.py
│   │   └── index.rst
│   ├── build/             # Built documentation (generated)
│   └── Makefile           # Makefile for building docs
├── pyproject.toml         # Project configuration and dependencies
├── .python-version        # Python version specification
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Contributing

1. Create a new branch for your feature: `git checkout -b feature-name`
2. Make your changes and format with black: `uv run black .`
3. Commit your changes: `git commit -m "Add feature"`
4. Push to the branch: `git push origin feature-name`
5. Create a Pull Request

## License

Please refer to the repository for license information.