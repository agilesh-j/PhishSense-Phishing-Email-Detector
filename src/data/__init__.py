"""Data ingestion, validation, deduplication, splitting, and loading modules."""
from .loader import (
    resolve_project_root,
    get_dataset_paths,
    load_and_validate_datasets,
    validate_split_file,
)

__all__ = [
    "resolve_project_root",
    "get_dataset_paths",
    "load_and_validate_datasets",
    "validate_split_file",
]
