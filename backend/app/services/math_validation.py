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