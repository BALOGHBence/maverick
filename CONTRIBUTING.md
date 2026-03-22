# Contributing guidelines

We appreciate your contributions in any shape and form.

Note that the [code of conduct](CODE_OF_CONDUCT.md) applies to all interactions with the project, including issues and pull requests.

When submitting pull requests, please follow the style guidelines of the project, ensure that your code is tested and documented, and write good commit messages, e.g., following [these guidelines](https://chris.beams.io/posts/git-commit/).

By submitting a pull request, you are licensing your code under the project [license](LICENSE.txt) and affirming that you either own copyright (automatic for most individuals) or are authorized to distribute under the project license (e.g., in case your employer retains copyright on your work).

## Windows note

`.claude/skills/maverick/SKILL.md` is a symlink pointing to `maverick-plugin/skills/api-consulting.md`. On macOS and Linux this works transparently. On Windows, git requires symlink support to be enabled — either turn on **Developer Mode** in Windows Settings, or run:

```bash
git config --global core.symlinks true
```

before cloning. Without this, the file is checked out as a plain text file containing the path string and the Claude Code skill will not work.
