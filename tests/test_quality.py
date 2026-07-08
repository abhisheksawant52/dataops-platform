"""Tests for the data-quality rules engine."""

import pandas as pd

from dataops import quality
from dataops.models import QualityRule, RuleType


def test_not_null_rule_flags_nulls():
    df = pd.DataFrame({"id": [1, 2, None, 4]})
    rule = QualityRule(name="id_not_null", rule_type=RuleType.NOT_NULL, column="id")

    result = quality.evaluate_rule(df, rule)

    assert result.passed is False
    assert result.observed["null_count"] == 1


def test_not_null_rule_passes_when_complete():
    df = pd.DataFrame({"id": [1, 2, 3]})
    rule = QualityRule(name="id_not_null", rule_type=RuleType.NOT_NULL, column="id")

    assert quality.evaluate_rule(df, rule).passed is True


def test_unique_and_range_rules():
    df = pd.DataFrame({"id": [1, 1, 2], "age": [10, 20, 200]})
    unique = QualityRule(name="id_unique", rule_type=RuleType.UNIQUE, column="id")
    in_range = QualityRule(
        name="age_range", rule_type=RuleType.IN_RANGE, column="age", params={"min": 0, "max": 120}
    )

    assert quality.evaluate_rule(df, unique).passed is False
    assert quality.evaluate_rule(df, in_range).passed is False


def test_report_marks_failed_when_any_rule_fails():
    df = pd.DataFrame({"email": ["a@example.com", "bad"]})
    rules = [
        QualityRule(
            name="email_format",
            rule_type=RuleType.REGEX_MATCH,
            column="email",
            params={"pattern": r"[^@]+@[^@]+\.[^@]+"},
        ),
        QualityRule(name="row_count", rule_type=RuleType.ROW_COUNT_BETWEEN, params={"min": 1}),
    ]

    report = quality.evaluate(df, rules, dataset="users")

    assert report.dataset == "users"
    assert report.passed is False
    assert len(report.failed_rules) == 1
