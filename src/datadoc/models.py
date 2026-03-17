"""Data models for DataDoc."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field


class DataType(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    BOOLEAN = "boolean"


class ColumnProfile(BaseModel):
    """Statistical profile for a single column."""

    name: str
    dtype: str
    inferred_type: DataType
    total_count: int
    null_count: int
    completeness: float = Field(ge=0.0, le=1.0)
    uniqueness: float = Field(ge=0.0, le=1.0)
    unique_count: int
    most_common: list[tuple[Any, int]] = Field(default_factory=list)
    # Numeric stats
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    min_val: float | None = None
    max_val: float | None = None
    # Distribution
    distribution: dict[str, int] = Field(default_factory=dict)


class ValidationRule(BaseModel):
    """A rule for validating data quality."""

    column: str
    rule_type: str  # type_check, range, pattern, not_null, unique, custom
    params: dict[str, Any] = Field(default_factory=dict)
    description: str = ""

    def check(self, series: pd.Series) -> tuple[bool, list[int]]:
        """Check rule against a series. Returns (passed, failing_indices)."""
        failing = []
        if self.rule_type == "not_null":
            failing = series.index[series.isna()].tolist()
        elif self.rule_type == "unique":
            dupes = series[series.duplicated(keep=False)]
            failing = dupes.index.tolist()
        elif self.rule_type == "type_check":
            expected = self.params.get("expected_type", "numeric")
            if expected == "numeric":
                for i, v in series.items():
                    if pd.notna(v):
                        try:
                            float(v)
                        except (ValueError, TypeError):
                            failing.append(i)
            elif expected == "datetime":
                for i, v in series.items():
                    if pd.notna(v):
                        try:
                            pd.to_datetime(v)
                        except (ValueError, TypeError):
                            failing.append(i)
        elif self.rule_type == "range":
            min_v = self.params.get("min")
            max_v = self.params.get("max")
            numeric = pd.to_numeric(series, errors="coerce")
            for i, v in numeric.items():
                if pd.notna(v):
                    if min_v is not None and v < min_v:
                        failing.append(i)
                    elif max_v is not None and v > max_v:
                        failing.append(i)
        elif self.rule_type == "pattern":
            pattern = self.params.get("regex", "")
            compiled = re.compile(pattern)
            for i, v in series.items():
                if pd.notna(v) and not compiled.match(str(v)):
                    failing.append(i)
        return len(failing) == 0, failing


class QualityReport(BaseModel):
    """Overall quality report for a dataset."""

    dataset_name: str
    row_count: int
    column_count: int
    profiles: list[ColumnProfile] = Field(default_factory=list)
    overall_completeness: float = 0.0
    overall_quality_score: float = 0.0
    validation_results: dict[str, dict[str, Any]] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    cleaning_actions: list[str] = Field(default_factory=list)


class Dataset(BaseModel):
    """Wrapper for a dataset with metadata."""

    model_config = {"arbitrary_types_allowed": True}

    name: str
    source: str = ""
    df: Any = None  # pd.DataFrame
    profile: QualityReport | None = None
