import pytest

from app.services.math_validation import (
    MathValidationError,
    are_math_expressions_equivalent,
    compare_math_expressions,
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

def test_math_comparison_distinguishes_correct_math():
    result = compare_math_expressions(
        "6 / 2",
        "3",
    )

    assert result.is_parseable is True
    assert result.is_equivalent is True


def test_math_comparison_distinguishes_incorrect_math():
    result = compare_math_expressions(
        "2",
        "3",
    )

    assert result.is_parseable is True
    assert result.is_equivalent is False


def test_math_comparison_distinguishes_non_math_answer():
    result = compare_math_expressions(
        "The Sun",
        "sun",
    )

    assert result.is_parseable is False
    assert result.is_equivalent is False
