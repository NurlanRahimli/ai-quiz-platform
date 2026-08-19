import pytest

from app.services.math_validation import (
    MathValidationError,
    are_math_expressions_equivalent,
    parse_math_expression,
)


@pytest.mark.parametrize(
    ("submitted", "expected"),
    [
        ("2x + 2x", "4x"),
        ("x + x", "2x"),
        ("x^2", "x*x"),
        ("2 * (x + 1)", "2x + 2"),
        ("5", "2 + 3"),
    ],
)
def test_equivalent_math_expressions(submitted, expected):
    assert are_math_expressions_equivalent(submitted, expected)


@pytest.mark.parametrize(
    ("submitted", "expected"),
    [
        ("2x + 1", "4x"),
        ("x^2", "x^3"),
        ("5", "6"),
    ],
)
def test_non_equivalent_math_expressions(submitted, expected):
    assert not are_math_expressions_equivalent(submitted, expected)


def test_invalid_math_expression_returns_false():
    assert not are_math_expressions_equivalent(
        "this is not math !!!",
        "4x",
    )


def test_empty_expression_cannot_be_parsed():
    with pytest.raises(MathValidationError):
        parse_math_expression("   ")