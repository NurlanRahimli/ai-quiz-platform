from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.quiz_attempt import QuizAttemptResultAnswer


PURPLE = colors.HexColor("#7C3AED")
PURPLE_DARK = colors.HexColor("#5B21B6")
PURPLE_LIGHT = colors.HexColor("#F5F3FF")

GREEN = colors.HexColor("#16A34A")
GREEN_LIGHT = colors.HexColor("#F0FDF4")

RED = colors.HexColor("#DC2626")
RED_LIGHT = colors.HexColor("#FEF2F2")

GRAY_50 = colors.HexColor("#F9FAFB")
GRAY_200 = colors.HexColor("#E5E7EB")
GRAY_500 = colors.HexColor("#6B7280")
GRAY_700 = colors.HexColor("#374151")
GRAY_900 = colors.HexColor("#111827")


def build_quiz_result_pdf(
    *,
    quiz_title: str,
    score: int,
    gradable_questions: int,
    total_questions: int,
    answers: list[QuizAttemptResultAnswer],
) -> bytes:
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=f"{quiz_title} - Quiz Results",
        author="QuizApp",
    )

    styles = getSampleStyleSheet()

    brand_style = ParagraphStyle(
        "Brand",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=PURPLE,
        spaceAfter=14,
    )

    title_style = ParagraphStyle(
        "QuizTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=29,
        textColor=GRAY_900,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=GRAY_500,
        spaceAfter=20,
    )

    score_label_style = ParagraphStyle(
        "ScoreLabel",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=GRAY_500,
    )

    score_style = ParagraphStyle(
        "Score",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=32,
        textColor=PURPLE_DARK,
    )

    question_number_style = ParagraphStyle(
        "QuestionNumber",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=PURPLE,
        spaceAfter=5,
    )

    question_style = ParagraphStyle(
        "Question",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=17,
        textColor=GRAY_900,
        spaceAfter=9,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=GRAY_700,
    )

    answer_label_style = ParagraphStyle(
        "AnswerLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=GRAY_500,
        spaceAfter=4,
    )

    ai_style = ParagraphStyle(
        "AI",
        parent=styles["Normal"],
        fontSize=9,
        leading=14,
        textColor=PURPLE_DARK,
    )

    percentage = (
        round((score / gradable_questions) * 100)
        if gradable_questions > 0
        else 0
    )

    incorrect_count = sum(
        answer.is_correct is False
        for answer in answers
    )

    ungraded_count = sum(
        answer.is_correct is None
        for answer in answers
    )

    story = [
        Paragraph("QUIZAPP", brand_style),
        Paragraph(quiz_title, title_style),
        Paragraph("Quiz Results", subtitle_style),
    ]

    score_table = Table(
        [
            [
                Paragraph("YOUR SCORE", score_label_style),
                Paragraph("CORRECT", score_label_style),
                Paragraph("INCORRECT", score_label_style),
                Paragraph("NOT GRADED", score_label_style),
            ],
            [
                Paragraph(f"{percentage}%", score_style),
                Paragraph(str(score), score_style),
                Paragraph(str(incorrect_count), score_style),
                Paragraph(str(ungraded_count), score_style),
            ],
        ],
        colWidths=[1.55 * inch] * 4,
        rowHeights=[0.34 * inch, 0.64 * inch],
    )

    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PURPLE_LIGHT),
                ("BOX", (0, 0), (-1, -1), 1, GRAY_200),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, GRAY_200),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    story.extend(
        [
            score_table,
            Spacer(1, 8),
            Paragraph(
                (
                    f"{score} of {gradable_questions} automatically graded "
                    f"questions correct · {total_questions} total questions"
                ),
                subtitle_style,
            ),
            Spacer(1, 10),
        ]
    )

    for index, answer in enumerate(answers, start=1):
        if answer.is_correct is True:
            status_text = "CORRECT"
            status_color = GREEN
            card_background = GREEN_LIGHT
        elif answer.is_correct is False:
            status_text = "INCORRECT"
            status_color = RED
            card_background = RED_LIGHT
        else:
            status_text = "NOT GRADED"
            status_color = PURPLE
            card_background = PURPLE_LIGHT

        status_style = ParagraphStyle(
            f"Status{index}",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            alignment=TA_CENTER,
            textColor=status_color,
        )

        header = Table(
            [
                [
                    Paragraph(
                        f"QUESTION {index}",
                        question_number_style,
                    ),
                    Paragraph(status_text, status_style),
                ]
            ],
            colWidths=[5.1 * inch, 1.1 * inch],
        )

        header.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        question_content = [
            header,
            Paragraph(answer.question_text, question_style),
            Paragraph("YOUR ANSWER", answer_label_style),
            Paragraph(
                answer.submitted_answer or "No answer submitted",
                body_style,
            ),
        ]

        if answer.correct_answer is not None:
            question_content.extend(
                [
                    Spacer(1, 8),
                    Paragraph("CORRECT ANSWER", answer_label_style),
                    Paragraph(answer.correct_answer, body_style),
                ]
            )

        if (
            answer.is_correct is False
            and answer.ai_explanation
        ):
            question_content.extend(
                [
                    Spacer(1, 10),
                    Table(
                        [
                            [
                                Paragraph(
                                    (
                                        "<b>EXPLANATION</b><br/>"
                                        f"{answer.ai_explanation}"
                                    ),
                                    ai_style,
                                )
                            ]
                        ],
                        colWidths=[5.9 * inch],
                        style=TableStyle(
                            [
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (-1, -1),
                                    PURPLE_LIGHT,
                                ),
                                (
                                    "BOX",
                                    (0, 0),
                                    (-1, -1),
                                    0.75,
                                    PURPLE,
                                ),
                                (
                                    "LEFTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    10,
                                ),
                                (
                                    "RIGHTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    10,
                                ),
                                (
                                    "TOPPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    9,
                                ),
                                (
                                    "BOTTOMPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    9,
                                ),
                            ]
                        ),
                    ),
                ]
            )

        card = Table(
            [[question_content]],
            colWidths=[6.2 * inch],
            style=TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        card_background,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.75,
                        GRAY_200,
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 14),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                    ("TOPPADDING", (0, 0), (-1, -1), 13),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 13),
                ]
            ),
        )

        story.extend(
            [
                KeepTogether(card),
                Spacer(1, 12),
            ]
        )

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes