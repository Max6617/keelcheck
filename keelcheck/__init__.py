"""keelcheck -- charter and audit.

One frozen human-approved original; requirements that name the mechanism upholding them
or are marked as wishes; gates kept as hashed locked code; an audit that reports
divergence from the original.
"""

# Kept in step with `[project] version` in pyproject.toml by the CI step that compares the two: a
# `--version` that disagrees with the packaged metadata is a number a user cannot act on.
__version__ = "0.1.0"

__all__ = ["__version__"]
