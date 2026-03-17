"""Tests for DataDoc."""

import numpy as np
import pandas as pd
import pytest

from datadoc.auditor.cleaner import DataCleaner
from datadoc.auditor.profiler import DataProfiler
from datadoc.auditor.validator import DataValidator
from datadoc.models import ColumnProfile, DataType, QualityReport, ValidationRule
from datadoc.report import render_report


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", None, "Diana", "Eve"],
        "age": [25, 30, 35, None, 28],
        "email": ["a@b.com", "b@c.com", "c@d.com", "d@e.com", "e@f.com"],
        "score": [88.5, 92.0, 76.3, 95.1, 84.0],
    })


@pytest.fixture
def dirty_df():
    return pd.DataFrame({
        "id": [1, 2, 2, 3, 4],
        "name": ["  Alice ", "BOB", "bob", None, "Diana  "],
        "value": [10, 20, 20, 1000, 15],
        "category": ["A", "B", None, "A", "C"],
    })


class TestDataProfiler:
    def test_profile_completeness(self, sample_df):
        profiler = DataProfiler()
        profiles = profiler.profile_dataframe(sample_df)
        name_profile = next(p for p in profiles if p.name == "name")
        assert name_profile.completeness == 0.8
        assert name_profile.null_count == 1

    def test_profile_uniqueness(self, sample_df):
        profiler = DataProfiler()
        profiles = profiler.profile_dataframe(sample_df)
        id_profile = next(p for p in profiles if p.name == "id")
        assert id_profile.uniqueness == 1.0

    def test_profile_numeric_stats(self, sample_df):
        profiler = DataProfiler()
        profiles = profiler.profile_dataframe(sample_df)
        score_profile = next(p for p in profiles if p.name == "score")
        assert score_profile.mean is not None
        assert score_profile.min_val == 76.3
        assert score_profile.max_val == 95.1

    def test_profile_inferred_types(self, sample_df):
        profiler = DataProfiler()
        profiles = profiler.profile_dataframe(sample_df)
        id_profile = next(p for p in profiles if p.name == "id")
        assert id_profile.inferred_type == DataType.NUMERIC

    def test_empty_dataframe(self):
        profiler = DataProfiler()
        profiles = profiler.profile_dataframe(pd.DataFrame({"a": pd.Series([], dtype=float)}))
        assert len(profiles) == 1
        assert profiles[0].completeness == 0.0


class TestDataValidator:
    def test_not_null_rule(self, sample_df):
        validator = DataValidator()
        validator.add_not_null("name")
        results = validator.validate(sample_df)
        assert not results["name must not be null"]["passed"]
        assert results["name must not be null"]["failing_count"] == 1

    def test_unique_rule(self, dirty_df):
        validator = DataValidator()
        validator.add_unique("id")
        results = validator.validate(dirty_df)
        assert not results["id must be unique"]["passed"]

    def test_range_rule(self, sample_df):
        validator = DataValidator()
        validator.add_range("score", min_val=0, max_val=100)
        results = validator.validate(sample_df)
        assert results["score must be in [0, 100]"]["passed"]

    def test_range_rule_fail(self, sample_df):
        validator = DataValidator()
        validator.add_range("score", min_val=80, max_val=100)
        results = validator.validate(sample_df)
        assert not results["score must be in [80, 100]"]["passed"]

    def test_pattern_rule(self, sample_df):
        validator = DataValidator()
        validator.add_pattern("email", r".+@.+\..+")
        results = validator.validate(sample_df)
        assert results[f"email must match .+@.+\\..+"]["passed"]

    def test_auto_rules(self, sample_df):
        validator = DataValidator()
        validator.auto_rules(sample_df)
        assert len(validator.rules) > 0

    def test_missing_column(self, sample_df):
        validator = DataValidator()
        validator.add_not_null("nonexistent")
        results = validator.validate(sample_df)
        assert not results["nonexistent must not be null"]["passed"]


class TestDataCleaner:
    def test_fill_nulls_auto(self, dirty_df):
        cleaner = DataCleaner()
        cleaned = cleaner.fill_nulls(dirty_df, strategy="auto")
        assert cleaned["name"].isna().sum() == 0
        assert cleaned["category"].isna().sum() == 0

    def test_remove_duplicates(self, dirty_df):
        cleaner = DataCleaner()
        cleaned = cleaner.remove_duplicates(dirty_df)
        assert len(cleaned) == 4

    def test_fix_outliers_iqr(self, dirty_df):
        cleaner = DataCleaner()
        cleaned = cleaner.fix_outliers(dirty_df, method="iqr")
        assert cleaned["value"].max() < 1000

    def test_standardize_formatting(self, dirty_df):
        cleaner = DataCleaner()
        cleaned = cleaner.standardize_formatting(dirty_df)
        assert cleaned["name"].iloc[0] == "alice"

    def test_full_clean(self, dirty_df):
        cleaner = DataCleaner()
        cleaned = cleaner.clean(dirty_df)
        assert len(cleaner.actions) > 0
        assert cleaned["category"].isna().sum() == 0

    def test_fill_nulls_mean(self):
        df = pd.DataFrame({"x": [1.0, 2.0, None, 4.0]})
        cleaner = DataCleaner()
        cleaned = cleaner.fill_nulls(df, strategy="mean")
        assert abs(cleaned["x"].iloc[2] - 2.3333) < 0.01


class TestModels:
    def test_validation_rule_not_null(self):
        rule = ValidationRule(column="a", rule_type="not_null")
        s = pd.Series([1, None, 3])
        passed, failing = rule.check(s)
        assert not passed
        assert 1 in failing

    def test_validation_rule_pattern(self):
        rule = ValidationRule(column="a", rule_type="pattern", params={"regex": r"^\d+$"})
        s = pd.Series(["123", "abc", "456"])
        passed, failing = rule.check(s)
        assert not passed
        assert 1 in failing

    def test_quality_report_model(self):
        report = QualityReport(
            dataset_name="test", row_count=100, column_count=5,
            overall_completeness=0.95, overall_quality_score=0.9,
        )
        assert report.dataset_name == "test"


class TestReport:
    def test_render_report(self):
        report = QualityReport(
            dataset_name="test.csv", row_count=100, column_count=3,
            overall_completeness=0.95, overall_quality_score=0.88,
            profiles=[
                ColumnProfile(
                    name="col1", dtype="int64", inferred_type=DataType.NUMERIC,
                    total_count=100, null_count=5, completeness=0.95,
                    uniqueness=0.8, unique_count=80,
                ),
            ],
            validation_results={"col1 not null": {"passed": False, "failing_count": 5}},
            issues=["col1 has low completeness"],
        )
        text = render_report(report)
        assert "test.csv" in text
        assert "95.0%" in text
