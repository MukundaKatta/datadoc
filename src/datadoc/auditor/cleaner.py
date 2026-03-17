"""Data cleaning - fix nulls, duplicates, outliers, formatting."""

from __future__ import annotations

import numpy as np
import pandas as pd


class DataCleaner:
    """Clean datasets by fixing common quality issues."""

    def __init__(self) -> None:
        self.actions: list[str] = []

    def fill_nulls(self, df: pd.DataFrame, strategy: str = "auto") -> pd.DataFrame:
        """Fill null values. strategy: auto, mean, median, mode, drop, constant."""
        df = df.copy()
        for col in df.columns:
            null_count = df[col].isna().sum()
            if null_count == 0:
                continue
            if strategy == "drop":
                df = df.dropna(subset=[col])
                self.actions.append(f"Dropped {null_count} rows with nulls in '{col}'")
            elif strategy == "mean" and pd.api.types.is_numeric_dtype(df[col]):
                val = df[col].mean()
                df[col] = df[col].fillna(val)
                self.actions.append(f"Filled {null_count} nulls in '{col}' with mean={val:.2f}")
            elif strategy == "median" and pd.api.types.is_numeric_dtype(df[col]):
                val = df[col].median()
                df[col] = df[col].fillna(val)
                self.actions.append(f"Filled {null_count} nulls in '{col}' with median={val:.2f}")
            elif strategy == "auto":
                if pd.api.types.is_numeric_dtype(df[col]):
                    val = df[col].median()
                    df[col] = df[col].fillna(val)
                    self.actions.append(f"Filled {null_count} nulls in '{col}' with median={val:.2f}")
                else:
                    val = df[col].mode().iloc[0] if not df[col].mode().empty else "unknown"
                    df[col] = df[col].fillna(val)
                    self.actions.append(f"Filled {null_count} nulls in '{col}' with mode='{val}'")
            else:
                val = df[col].mode().iloc[0] if not df[col].mode().empty else "unknown"
                df[col] = df[col].fillna(val)
                self.actions.append(f"Filled {null_count} nulls in '{col}' with mode='{val}'")
        return df

    def remove_duplicates(self, df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
        """Remove duplicate rows."""
        df = df.copy()
        n_before = len(df)
        df = df.drop_duplicates(subset=subset)
        removed = n_before - len(df)
        if removed > 0:
            self.actions.append(f"Removed {removed} duplicate rows")
        return df

    def fix_outliers(self, df: pd.DataFrame, method: str = "iqr", factor: float = 1.5) -> pd.DataFrame:
        """Cap outliers using IQR or z-score method."""
        df = df.copy()
        for col in df.select_dtypes(include=[np.number]).columns:
            if method == "iqr":
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - factor * iqr
                upper = q3 + factor * iqr
            else:  # zscore
                mean = df[col].mean()
                std = df[col].std()
                lower = mean - factor * std
                upper = mean + factor * std
            outliers = ((df[col] < lower) | (df[col] > upper)).sum()
            if outliers > 0:
                df[col] = df[col].clip(lower, upper)
                self.actions.append(f"Capped {outliers} outliers in '{col}' to [{lower:.2f}, {upper:.2f}]")
        return df

    def standardize_formatting(self, df: pd.DataFrame) -> pd.DataFrame:
        """Strip whitespace, lowercase string columns."""
        df = df.copy()
        for col in df.select_dtypes(include=["object"]).columns:
            original = df[col].copy()
            df[col] = df[col].astype(str).str.strip().str.lower()
            # Restore NaN
            df.loc[original.isna(), col] = np.nan
            changed = (original.dropna() != df[col].dropna()).sum()
            if changed > 0:
                self.actions.append(f"Standardized formatting for {changed} values in '{col}'")
        return df

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run full cleaning pipeline."""
        self.actions = []
        df = self.remove_duplicates(df)
        df = self.fix_outliers(df)
        df = self.standardize_formatting(df)
        df = self.fill_nulls(df, strategy="auto")
        return df
