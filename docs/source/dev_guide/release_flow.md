# Release Flow

## Create an annotated tag on the current main HEAD

```shell
git checkout main
git pull origin
git tag -a v0.1.0 -m "Release v0.1.0"
```

## Push the tag

```shell
git push origin v0.1.0
```

## Publish the GitHub Release

On GitHub:

- Releases → Draft a new release
- Choose existing tag: v0.1.0
- Target: main
- Publish Release

**This triggers PyPI deployment automatically**.
