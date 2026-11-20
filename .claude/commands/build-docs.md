# Build the Sphinx documentation for the given target

Run this shell command, replacing `$ARGUMENTS` with the provided target (default: `html`):

```sh
uv run sphinx-build -b $ARGUMENTS docs/source docs/build/$ARGUMENTS
```

If no argument is given, use `html` as the target.
