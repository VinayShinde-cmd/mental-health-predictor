import pytest

from app.domain.features import FIELD_LIMITS, TRAINING_RANGES, training_range_warnings
from app.domain.interpretation import describe_score


@pytest.mark.parametrize(
    ("score", "band"),
    [
        (3.6, "below_typical"),
        (5.09, "below_typical"),
        (5.1, "typical"),
        (6.1, "typical"),
        (7.1, "typical"),
        (7.11, "above_typical"),
        (9.4, "above_typical"),
    ],
)
def test_bands_follow_the_training_quartiles(score, band):
    assert describe_score(score).band == band


def test_score_is_rounded_to_two_decimals():
    assert describe_score(6.123456).score == 6.12


def test_no_warnings_inside_the_training_range():
    values = {"age": 21, "sleep_hours_per_night": 7.0, "avg_daily_usage_hours": 4.0}
    assert training_range_warnings(values) == []


def test_warnings_name_the_field_and_the_trained_range():
    warnings = training_range_warnings({"age": 35, "sleep_hours_per_night": 2.0})
    assert len(warnings) == 2
    assert "Age (35)" in warnings[0]
    assert "18 to 24" in warnings[0]
    assert "Sleep (2)" in warnings[1]


def test_every_training_range_sits_inside_the_accepted_limits():
    for field, trained in TRAINING_RANGES.items():
        assert FIELD_LIMITS[field].min <= trained.min <= trained.max <= FIELD_LIMITS[field].max
