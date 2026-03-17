"""Data profiling - compute statistics per column."""

from __future__ import annotations

import numpy as np
import pandas as pd

from datadoc.models import ColumnProfile, DataType


class DataProfiler:
    """Compute completeness, uniqueness, and distribution per column."""

    def profile_dataframe(self, df: pd.DataFrame) -> list[ColumnProfile]:
        """Profile every column in a DataFrame."""
        return [self._profile_column(df[col]) for col in df.columns]

    def _infer_type(self, series: pd.Series) -> DataType:
        if pd.api.types.is_bool_dtype(series):
            return DataType.BOOLEAN
        if pd.api.types.is_numeric_dtype(series):
            return DataType.NUMERIC
        if pd.api.types.is_datetime64_any_dtype(series):
            return DataType.DATETIME
        non_null = series.dropna()
        if len(non_null) == 0:
            return DataType.TEXT
        # Try datetime parse
        try:
            pd.to_datetime(non_null.head(20))
            return DataType.DATETIME
        except (ValueError, TypeError):
            pass
        nunique = non_null.nunique()
        if nunique / max(len(non_null), 1) < 0.5:
            return DataType.CATEGORICAL
        return DataType.TEXT

    def _profile_column(self, series: pd.Series) -> ColumnProfile:
        total = len(series)
        null_count = int(series.isna().sum())
        non_null = series.dropna()
        unique_count = int(non_null.nunique())
        completeness = (total - null_count) / total if total > 0 else 0.0
        uniqueness = unique_count / len(non_null) if len(non_null) > 0 else 0.0
        inferred = self._infer_type(series)

        # Most common values
        vc = series.value_counts().head(5)
        most_common = [(str(k), int(v)) for k, v in vc.items()]

        # Distribution buckets
        distribution: dict[str, int] = {}
        if inferred == DataType.NUMERIC:
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            if len(numeric) > 0:
                counts, edges = np.histogram(numeric, bins=min(10, len(numeric)))
                for i, c in enumerate(counts):
                    label = f"{edges[i]:.2f}-{edges[i+1]:.2f}"
                    distribution[label] = int(c)
        else:
            for k, v in vc.head(10).items():
                distribution[str(k)] = int(v)

        profile = ColumnProfile(
            name=series.name,
            dtype=str(series.dtype),
            inferred_type=inferred,
            total_count=total,
            null_count=null_count,
            completeness=round(completeness, 4),
            uniqueness=round(uniqueness, 4),
            unique_count=unique_count,
            most_common=most_common,
            distribution=distribution,
        )

        if inferred == DataType.NUMERIC:
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            if len(numeric) > 0:
                profile.mean = round(float(numeric.mean()), 4)
                profile.median = round(float(numeric.median()), 4)
                profile.std = round(float(numeric.std()), 4)
                profile.min_val = float(numeric.min())
                profile.max_val = float(numeric.max())

        return profile
