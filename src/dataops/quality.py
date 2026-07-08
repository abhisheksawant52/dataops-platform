"""Lightweight data-quality rules engine.

Rules (``expectations``) are evaluated against a :class:`pandas.DataFrame` and
produce a :class:`~dataops.models.QualityReport`. This is a deliberately small,
dependency-light alternative to heavyweight frameworks: each expectation is a
pure function over a column (or the whole frame) that returns a
:class:`~dataops.models.RuleResult`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

import pandas as pd

from .models import QualityReport, QualityRule, RuleResult, RuleType


def _missing_column(rule: QualityRule) -> RuleResult:
    return RuleResult(
        rule=rule.name,
        rule_type=rule.rule_type,
        column=rule.column,
        passed=False,
        message=f"column '{rule.column}' not found in dataframe",
    )


def _check_not_null(df: pd.DataFrame, rule: QualityRule) -> RuleResult:
    null_count = int(df[rule.column].isna().sum())
    return RuleResult(
        rule=rule.name,
        rule_type=rule.rule_type,
        column=rule.column,
        passed=null_count == 0,
        observed={"null_count": null_count},
        message=f"{null_count} null value(s) found",
    )


def _check_unique(df: pd.DataFrame, rule: QualityRule) -> RuleResult:
    duplicate_count = int(df[rule.column].duplicated().sum())
    return RuleResult(
        rule=rule.name,
        rule_type=rule.rule_type,
        column=rule.column,
        passed=duplicate_count == 0,
        observed={"duplicate_count": duplicate_count},
        message=f"{duplicate_count} duplicate value(s) found",
    )


def _check_in_range(df: pd.DataFrame, rule: QualityRule) -> RuleResult:
    minimum = rule.params.get("min")
    maximum = rule.params.get("max")
    series = pd.to_numeric(df[rule.column], errors="coerce")
    below = series < minimum if minimum is not None else pd.Series(False, index=series.index)
    above = series > maximum if maximum is not None else pd.Series(False, index=series.index)
    violations = int((below | above | series.isna()).sum())
    return RuleResult(
        rule=rule.name,
        rule_type=rule.rule_type,
        column=rule.column,
        passed=violations == 0,
        observed={"violations": violations, "min": minimum, "max": maximum},
        message=f"{violations} value(s) outside [{minimum}, {maximum}]",
    )


def _check_regex_match(df: pd.DataFrame, rule: QualityRule) -> RuleResult:
    pattern = rule.params.get("pattern", "")
    compiled = re.compile(pattern)
    values = df[rule.column].astype(str)
    mismatches = int((~values.map(lambda v: compiled.fullmatch(v) is not None)).sum())
    return RuleResult(
        rule=rule.name,
        rule_type=rule.rule_type,
        column=rule.column,
        passed=mismatches == 0,
        observed={"mismatches": mismatches, "pattern": pattern},
        message=f"{mismatches} value(s) did not match /{pattern}/",
    )


def _check_row_count_between(df: pd.DataFrame, rule: QualityRule) -> RuleResult:
    minimum = rule.params.get("min", 0)
    maximum = rule.params.get("max")
    count = int(len(df))
    passed = count >= minimum and (maximum is None or count <= maximum)
    return RuleResult(
        rule=rule.name,
        rule_type=rule.rule_type,
        column=None,
        passed=passed,
        observed={"row_count": count, "min": minimum, "max": maximum},
        message=f"row count {count} not in [{minimum}, {maximum}]",
    )


_COLUMN_RULES = {
    RuleType.NOT_NULL: _check_not_null,
    RuleType.UNIQUE: _check_unique,
    RuleType.IN_RANGE: _check_in_range,
    RuleType.REGEX_MATCH: _check_regex_match,
}


def evaluate_rule(df: pd.DataFrame, rule: QualityRule) -> RuleResult:
    """Evaluate a single quality rule against *df*."""
    if rule.rule_type == RuleType.ROW_COUNT_BETWEEN:
        return _check_row_count_between(df, rule)

    if rule.column is None or rule.column not in df.columns:
        return _missing_column(rule)

    handler = _COLUMN_RULES[rule.rule_type]
    return handler(df, rule)


def evaluate(
    df: pd.DataFrame,
    rules: Iterable[QualityRule],
    dataset: str = "dataset",
    fail_threshold: float = 0.0,
) -> QualityReport:
    """Evaluate *rules* over *df* and return an aggregated report.

    Parameters
    ----------
    df:
        The dataframe to validate.
    rules:
        Quality rules to apply.
    dataset:
        Logical dataset name recorded on the report.
    fail_threshold:
        Fraction (0.0-1.0) of failing rules tolerated before the overall
        report is marked as failed. ``0.0`` means any failure fails the report.
    """
    results = [evaluate_rule(df, rule) for rule in rules]
    total = len(results)
    failures = sum(1 for r in results if not r.passed)
    failed_fraction = (failures / total) if total else 0.0
    return QualityReport(
        dataset=dataset,
        results=results,
        passed=failed_fraction <= fail_threshold,
    )
