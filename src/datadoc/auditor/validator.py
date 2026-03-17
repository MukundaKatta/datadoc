"""Data validation - check types, ranges, patterns, constraints."""

from __future__ import annotations

from typing import Any

import pandas as pd

from datadoc.models import ValidationRule


class DataValidator:
    """Validate data against a set of rules."""

    def __init__(self) -> None:
        self.rules: list[ValidationRule] = []

    def add_rule(self, rule: ValidationRule) -> None:
        self.rules.append(rule)

    def add_not_null(self, column: str) -> None:
        self.add_rule(ValidationRule(
            column=column, rule_type="not_null",
            description=f"{column} must not be null",
        ))

    def add_unique(self, column: str) -> None:
        self.add_rule(ValidationRule(
            column=column, rule_type="unique",
            description=f"{column} must be unique",
        ))

    def add_type_check(self, column: str, expected_type: str) -> None:
        self.add_rule(ValidationRule(
            column=column, rule_type="type_check",
            params={"expected_type": expected_type},
            description=f"{column} must be {expected_type}",
        ))

    def add_range(self, column: str, min_val: float | None = None, max_val: float | None = None) -> None:
        params: dict[str, Any] = {}
        if min_val is not None:
            params["min"] = min_val
        if max_val is not None:
            params["max"] = max_val
        self.add_rule(ValidationRule(
            column=column, rule_type="range", params=params,
            description=f"{column} must be in [{min_val}, {max_val}]",
        ))

    def add_pattern(self, column: str, regex: str) -> None:
        self.add_rule(ValidationRule(
            column=column, rule_type="pattern",
            params={"regex": regex},
            description=f"{column} must match {regex}",
        ))

    def validate(self, df: pd.DataFrame) -> dict[str, dict[str, Any]]:
        """Run all rules against the DataFrame. Returns {rule_desc: {passed, failing_count, failing_indices}}."""
        results: dict[str, dict[str, Any]] = {}
        for rule in self.rules:
            if rule.column not in df.columns:
                results[rule.description] = {
                    "passed": False, "error": "column not found",
                    "failing_count": -1, "failing_indices": [],
                }
                continue
            passed, failing = rule.check(df[rule.column])
            results[rule.description] = {
                "passed": passed,
                "failing_count": len(failing),
                "failing_indices": failing[:100],  # cap for display
            }
        return results

    def auto_rules(self, df: pd.DataFrame) -> None:
        """Generate sensible default rules from data shape."""
        for col in df.columns:
            self.add_not_null(col)
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric = pd.to_numeric(df[col], errors="coerce").dropna()
                if len(numeric) > 0:
                    self.add_range(col, float(numeric.min()), float(numeric.max()))
