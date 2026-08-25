import re

from sympy import simplify
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


class MathValidationError(ValueError):
    pass


class MathComparisonResult:
    def __init__(
        self,
        *,
        is_parseable: bool,
        is_equivalent: bool,
    ):
        self.is_parseable = is_parseable
        self.is_equivalent = is_equivalent


def parse_math_expression(expression: str):
    cleaned_expression = expression.strip()

    if not cleaned_expression:
        raise MathValidationError("Math expression cannot be empty")

    try:
        return parse_expr(
            cleaned_expression,
            transformations=TRANSFORMATIONS,
            evaluate=True,
        )
    except Exception as exc:
        raise MathValidationError(
            "Unable to parse math expression"
        ) from exc


def are_math_expressions_equivalent(
    submitted_answer: str,
    expected_answer: str,
) -> bool:
    try:
        submitted = parse_math_expression(submitted_answer)
        expected = parse_math_expression(expected_answer)
    except MathValidationError:
        return False

    try:
        return simplify(submitted - expected) == 0
    except Exception:
        return False

def looks_like_math_expression(expression: str) -> bool:
    cleaned_expression = expression.strip()

    if not cleaned_expression:
        return False

    words = re.findall(r"[A-Za-z]{2,}", cleaned_expression)

    allowed_math_words = {
        "sin",
        "cos",
        "tan",
        "sqrt",
        "log",
        "ln",
        "pi",
        "exp",
    }

    return all(
        word.lower() in allowed_math_words
        for word in words
    )


def compare_math_expressions(
    submitted_answer: str,
    expected_answer: str,
) -> MathComparisonResult:
    if (
        not looks_like_math_expression(submitted_answer)
        or not looks_like_math_expression(expected_answer)
    ):
        return MathComparisonResult(
            is_parseable=False,
            is_equivalent=False,
        )

    try:
        submitted = parse_math_expression(submitted_answer)
        expected = parse_math_expression(expected_answer)
    except MathValidationError:
        return MathComparisonResult(
            is_parseable=False,
            is_equivalent=False,
        )

    try:
        is_equivalent = simplify(submitted - expected) == 0
    except Exception:
        return MathComparisonResult(
            is_parseable=False,
            is_equivalent=False,
        )

    return MathComparisonResult(
        is_parseable=True,
        is_equivalent=bool(is_equivalent),
    )
