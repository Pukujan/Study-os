"""Versioned curriculum loading and cross-file validation."""

from .loader import CurriculumSlice, CurriculumValidationError, load_curriculum_slice, validate_curriculum_pair

__all__ = [
    "CurriculumSlice",
    "CurriculumValidationError",
    "load_curriculum_slice",
    "validate_curriculum_pair",
]
