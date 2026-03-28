#!/usr/bin/env bash
# Build Sphinx documentation for Maverick.
# Usage: build.sh [TARGET]
# TARGET defaults to "html" if not provided.

set -euo pipefail

TARGET="${1:-html}"
SOURCE_DIR="docs/source"
BUILD_DIR="docs/build/${TARGET}"

echo "Building Sphinx documentation (target: ${TARGET})..."

uv run sphinx-build -b "${TARGET}" "${SOURCE_DIR}" "${BUILD_DIR}"

echo ""
echo "Build complete. Output: ${BUILD_DIR}"
