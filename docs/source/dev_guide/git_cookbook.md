# Git Cookbook

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
