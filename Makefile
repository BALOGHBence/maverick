SPHINXOPTS ?=
SOURCEDIR  = docs/source
BUILDDIR   = docs/build

.PHONY: docs docs-clean

# Build the HTML documentation into docs/build/html.
docs:
	uv run sphinx-build -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS)

# Remove the build output, then rebuild the HTML documentation from scratch.
docs-clean:
	rm -rf "$(BUILDDIR)"
	$(MAKE) docs
