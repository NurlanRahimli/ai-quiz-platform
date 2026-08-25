import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from datetime import date, datetime, time, timedelta

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_attempt_answer import QuizAttemptAnswer
from app.models.user import User
from app.schemas.quiz_attempt import (
    QuizAttemptHistoryItem,
    QuizAttemptResponse,
    QuizAttemptResultAnswer,
    QuizAttemptResultResponse,
    QuizAttemptSubmit,
    QuizAttemptResultChoice,
    UserAttemptQuizItem,
    UserAttemptQuizPage,
    GuestQuizAttemptResultResponse,
)
from app.services.whiteboard_storage_service import (
    WhiteboardImageValidationError,
    save_whiteboard_image,
)
from app.services.quiz_grading import grade_attempt_answer
from app.services.math_validation import compare_math_expressions
from app.services.ai_service import (
    evaluate_math_answer,
    evaluate_written_answer,
    generate_incorrect_answer_explanation,
)
from app.services.quiz_result_pdf import build_quiz_result_pdf
from app.models.audit_log import AuditLog


router = APIRouter(
    prefix="/quizzes",
    tags=["Quiz Attempts"],
)

user_attempts_router = APIRouter(
    prefix="/attempts",
    tags=["Quiz Attempts"],
)


@user_attempts_router.get(
    "",
    response_model=UserAttemptQuizPage,
)
def get_current_user_attempts(
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    category: str | None = None,
    score_range: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserAttemptQuizPage:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from cannot be later than date_to",
        )

    allowed_score_ranges = {
        "90-100",
        "80-89",
        "70-79",
        "below-70",
    }

    if (
        score_range is not None
        and score_range not in allowed_score_ranges
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid score range",
        )

    filters = [
        QuizAttempt.user_id == current_user.id,
    ]

    if search is not None and search.strip():
        filters.append(
            Quiz.title.ilike(
                f"%{search.strip()}%"
            )
        )

    if category is not None and category.strip():
        filters.append(
            Quiz.category.ilike(category.strip())
        )

    if date_from is not None:
        filters.append(
            QuizAttempt.submitted_at >= datetime.combine(
                date_from,
                time.min,
            )
        )

    if date_to is not None:
        filters.append(
            QuizAttempt.submitted_at < datetime.combine(
                date_to + timedelta(days=1),
                time.min,
            )
        )

    attempts = db.scalars(
        select(QuizAttempt)
        .options(
            selectinload(QuizAttempt.quiz),
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.question)
            .selectinload(Question.answer_choices),
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.selected_choice),
        )
        .join(
            Quiz,
            Quiz.id == QuizAttempt.quiz_id,
        )
        .where(*filters)
        .order_by(
            QuizAttempt.submitted_at.desc(),
            QuizAttempt.id.desc(),
        )
    ).all()

    quiz_history: dict[uuid.UUID, UserAttemptQuizItem] = {}
    quiz_score_totals: dict[uuid.UUID, float] = {}
    quiz_graded_attempt_counts: dict[uuid.UUID, int] = {}

    for attempt in attempts:
        score = 0
        gradable_questions = 0

        for answer in attempt.answers:
            is_correct = grade_attempt_answer(
                answer.question,
                answer,
            )

            if is_correct is not None:
                gradable_questions += 1

                if is_correct:
                    score += 1

        score_percentage = (
            (score / gradable_questions) * 100
            if gradable_questions > 0
            else None
        )

        if score_range:
            if score_percentage is None:
                continue

            if (
                score_range == "90-100"
                and not 90 <= score_percentage <= 100
            ):
                continue

            if (
                score_range == "80-89"
                and not 80 <= score_percentage < 90
            ):
                continue

            if (
                score_range == "70-79"
                and not 70 <= score_percentage < 80
            ):
                continue

            if (
                score_range == "below-70"
                and not score_percentage < 70
            ):
                continue

        existing_quiz = quiz_history.get(attempt.quiz_id)

        if existing_quiz is None:
            quiz_history[attempt.quiz_id] = UserAttemptQuizItem(
                quiz_id=attempt.quiz_id,
                quiz_title=attempt.quiz.title,
                quiz_category=attempt.quiz.category,
                latest_attempt_id=attempt.id,
                average_score=None,
                latest_submitted_at=attempt.submitted_at,
                latest_score=score,
                latest_gradable_questions=gradable_questions,
                latest_total_questions=len(attempt.answers),
                attempt_count=1,
            )
        else:
            existing_quiz.attempt_count += 1

        if score_percentage is not None:
            quiz_score_totals[attempt.quiz_id] = (
                quiz_score_totals.get(attempt.quiz_id, 0.0)
                + score_percentage
            )
            quiz_graded_attempt_counts[attempt.quiz_id] = (
                quiz_graded_attempt_counts.get(attempt.quiz_id, 0)
                + 1
            )

    for quiz_id, quiz_item in quiz_history.items():
        graded_attempt_count = quiz_graded_attempt_counts.get(
            quiz_id,
            0,
        )

        if graded_attempt_count > 0:
            quiz_item.average_score = round(
                quiz_score_totals[quiz_id] / graded_attempt_count,
                2,
            )

    quizzes = list(quiz_history.values())

    total = len(quizzes)

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    start = (page - 1) * page_size
    end = start + page_size

    paginated_quizzes = quizzes[start:end]

    return UserAttemptQuizPage(
        quizzes=paginated_quizzes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/{quiz_id}/attempts/guest",
    response_model=GuestQuizAttemptResultResponse,
)
def submit_guest_quiz_attempt(
    quiz_id: uuid.UUID,
    attempt_data: QuizAttemptSubmit,
    db: Session = Depends(get_db),
) -> GuestQuizAttemptResultResponse:
    quiz = db.scalar(
        select(Quiz)
        .options(
            selectinload(Quiz.questions)
            .selectinload(Question.answer_choices)
        )
        .where(Quiz.id == quiz_id)
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    questions = {
        question.id: question
        for question in quiz.questions
    }

    submitted_question_ids = [
        answer.question_id
        for answer in attempt_data.answers
    ]

    if len(submitted_question_ids) != len(set(submitted_question_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Each question can only be answered once",
        )

    if set(submitted_question_ids) != set(questions):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="An answer must be provided for every quiz question",
        )

    result_answers: list[QuizAttemptResultAnswer] = []
    score = 0
    gradable_questions = 0

    for submitted_answer in attempt_data.answers:
        question = questions[submitted_answer.question_id]

        if (
            question.question_type != "math_work"
            and submitted_answer.whiteboard_image is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Only math-work questions can include "
                    "a whiteboard image"
                ),
            )

        if question.question_type == "multiple_choice":
            if submitted_answer.text_answer is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Multiple-choice questions cannot include "
                        "a text answer"
                    ),
                )

            valid_choice_ids = {
                choice.id
                for choice in question.answer_choices
            }

            if (
                submitted_answer.selected_choice_id is not None
                and submitted_answer.selected_choice_id
                not in valid_choice_ids
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Selected answer choice does not belong "
                        "to this question"
                    ),
                )

        elif question.question_type in {
            "written_answer",
            "math_work",
        }:
            if submitted_answer.selected_choice_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Written and math questions cannot include "
                        "a selected choice"
                    ),
                )

            if (
                submitted_answer.text_answer is not None
                and not submitted_answer.text_answer.strip()
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Written and math questions cannot contain "
                        "an empty text answer"
                    ),
                )

            submitted_answer.text_answer = (
                submitted_answer.text_answer.strip()
                if submitted_answer.text_answer is not None
                else None
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported question type",
            )

        temporary_answer = QuizAttemptAnswer(
            question_id=question.id,
            selected_choice_id=submitted_answer.selected_choice_id,
            text_answer=submitted_answer.text_answer,
        )

        temporary_answer.question = question

        if question.question_type == "multiple_choice":
            temporary_answer.selected_choice = next(
                (
                    choice
                    for choice in question.answer_choices
                    if choice.id
                    == submitted_answer.selected_choice_id
                ),
                None,
            )

        is_correct = grade_attempt_answer(
            question,
            temporary_answer,
        )

        if is_correct is not None:
            gradable_questions += 1

            if is_correct:
                score += 1

        answer_choices: list[QuizAttemptResultChoice] = []

        if question.question_type == "multiple_choice":
            selected_choice = temporary_answer.selected_choice

            submitted_answer_text = (
                selected_choice.text
                if selected_choice
                else ""
            )

            correct_choice = next(
                (
                    choice
                    for choice in question.answer_choices
                    if choice.is_correct
                ),
                None,
            )

            correct_answer = (
                correct_choice.text
                if correct_choice
                else None
            )

            answer_choices = [
                QuizAttemptResultChoice(
                    id=choice.id,
                    text=choice.text,
                    is_correct=choice.is_correct,
                    was_selected=(
                        choice.id
                        == submitted_answer.selected_choice_id
                    ),
                    position=choice.position,
                )
                for choice in sorted(
                    question.answer_choices,
                    key=lambda choice: choice.position,
                )
            ]

        elif question.question_type == "math_work":
            submitted_answer_text = (
                submitted_answer.text_answer or ""
            )
            correct_answer = question.expected_answer

        else:
            submitted_answer_text = (
                submitted_answer.text_answer or ""
            )
            correct_answer = None

        result_answers.append(
            QuizAttemptResultAnswer(
                answer_choices=answer_choices,
                question_id=question.id,
                question_text=question.text,
                question_type=question.question_type,
                is_correct=is_correct,
                submitted_answer=submitted_answer_text,
                correct_answer=correct_answer,
            )
        )

    return GuestQuizAttemptResultResponse(
        quiz_id=quiz.id,
        score=score,
        gradable_questions=gradable_questions,
        total_questions=len(quiz.questions),
        answers=result_answers,
    )


@router.post(
    "/{quiz_id}/attempts",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_quiz_attempt(
    quiz_id: uuid.UUID,
    attempt_data: QuizAttemptSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizAttempt:
    quiz = db.scalar(
        select(Quiz)
        .options(
            selectinload(Quiz.questions)
            .selectinload(Question.answer_choices)
        )
        .where(Quiz.id == quiz_id)
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    questions = {
        question.id: question
        for question in quiz.questions
    }

    submitted_question_ids = [
        answer.question_id
        for answer in attempt_data.answers
    ]

    if len(submitted_question_ids) != len(set(submitted_question_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Each question can only be answered once",
        )

    if set(submitted_question_ids) != set(questions):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="An answer must be provided for every quiz question",
        )

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
    )

    for submitted_answer in attempt_data.answers:
        question = questions[submitted_answer.question_id]

        if (
            question.question_type != "math_work"
            and submitted_answer.whiteboard_image is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Only math-work questions can include "
                    "a whiteboard image"
                ),
            )

        if question.question_type == "multiple_choice":
            if submitted_answer.text_answer is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Multiple-choice questions cannot include "
                        "a text answer"
                    ),
                )

            valid_choice_ids = {
                choice.id
                for choice in question.answer_choices
            }

            if (
                submitted_answer.selected_choice_id is not None
                and submitted_answer.selected_choice_id not in valid_choice_ids
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Selected answer choice does not belong "
                        "to this question"
                    ),
                )

        elif question.question_type in {
            "written_answer",
            "math_work",
        }:
            if submitted_answer.selected_choice_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Written and math questions cannot include "
                        "a selected choice"
                    ),
                )

            if (
                submitted_answer.text_answer is not None
                and not submitted_answer.text_answer.strip()
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Written and math questions cannot contain "
                        "an empty text answer"
                    ),
                )

            submitted_answer.text_answer = (
                submitted_answer.text_answer.strip()
                if submitted_answer.text_answer is not None
                else None
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported question type",
            )

        whiteboard_image_url = None

        if submitted_answer.whiteboard_image is not None:
            try:
                whiteboard_image_url = save_whiteboard_image(
                    submitted_answer.whiteboard_image,
                    attempt_id=attempt.id,
                    question_id=question.id,
                )
            except WhiteboardImageValidationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=str(exc),
                ) from exc

        ai_is_correct = None
        ai_explanation = None

        if question.question_type == "multiple_choice":
            selected_choice = next(
                (
                    choice
                    for choice in question.answer_choices
                    if choice.id == submitted_answer.selected_choice_id
                ),
                None,
            )
            correct_choice = next(
                (
                    choice
                    for choice in question.answer_choices
                    if choice.is_correct
                ),
                None,
            )

            if (
                selected_choice is not None
                and correct_choice is not None
                and not selected_choice.is_correct
            ):
                try:
                    explanation = generate_incorrect_answer_explanation(
                        question_text=question.text,
                        submitted_answer=selected_choice.text,
                        correct_answer=correct_choice.text,
                    )
                except RuntimeError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=(
                            "Unable to generate the answer explanation "
                            "right now. Please try again."
                        ),
                    ) from exc

                ai_explanation = explanation.explanation

        if (
            question.question_type == "written_answer"
            and submitted_answer.text_answer is not None
        ):
            try:
                evaluation = evaluate_written_answer(
                    question_text=question.text,
                    submitted_answer=submitted_answer.text_answer,
                )
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "Unable to evaluate the written answer right now. "
                        "Please try again."
                    ),
                ) from exc

            ai_is_correct = evaluation.is_correct

            if not evaluation.is_correct:
                ai_explanation = evaluation.explanation

        if (
            question.question_type == "math_work"
            and submitted_answer.text_answer is not None
            and question.expected_answer
        ):
            comparison = compare_math_expressions(
                submitted_answer.text_answer,
                question.expected_answer,
            )

            if comparison.is_parseable:
                ai_is_correct = comparison.is_equivalent

                if not comparison.is_equivalent:
                    try:
                        explanation = generate_incorrect_answer_explanation(
                            question_text=question.text,
                            submitted_answer=submitted_answer.text_answer,
                            correct_answer=question.expected_answer,
                        )
                    except RuntimeError as exc:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=(
                                "Unable to generate the answer explanation "
                                "right now. Please try again."
                            ),
                        ) from exc

                    ai_explanation = explanation.explanation

            else:
                try:
                    evaluation = evaluate_math_answer(
                        question_text=question.text,
                        submitted_answer=submitted_answer.text_answer,
                        expected_answer=question.expected_answer,
                    )
                except RuntimeError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=(
                            "Unable to evaluate the answer right now. "
                            "Please try again."
                        ),
                    ) from exc

                ai_is_correct = evaluation.is_correct

                if not evaluation.is_correct:
                    ai_explanation = evaluation.explanation

        attempt.answers.append(
            QuizAttemptAnswer(
                question_id=question.id,
                selected_choice_id=(
                    submitted_answer.selected_choice_id
                ),
                text_answer=submitted_answer.text_answer,
                whiteboard_image_url=whiteboard_image_url,
                ai_is_correct=ai_is_correct,
                ai_explanation=ai_explanation,
            )
        )


    quiz_creator = db.scalar(
        select(User).where(User.id == quiz.owner_id)
    )

    if quiz_creator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz creator not found",
        )

    audit_log = AuditLog(
        user_id=current_user.id,
        quiz_id=quiz.id,
        action="quiz_completed",
        quiz_title=quiz.title,
        creator_name=quiz_creator.display_name,
    )

    db.add(audit_log)


    db.add(attempt)
    db.commit()

    saved_attempt = db.scalar(
        select(QuizAttempt)
        .options(selectinload(QuizAttempt.answers))
        .where(QuizAttempt.id == attempt.id)
    )

    return saved_attempt


@router.get(
    "/{quiz_id}/attempts",
    response_model=list[QuizAttemptHistoryItem],
)
def get_quiz_attempt_history(
    quiz_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[QuizAttemptHistoryItem]:
    quiz = db.scalar(
        select(Quiz).where(
            Quiz.id == quiz_id,
            Quiz.owner_id == current_user.id,
        )
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    attempts = db.scalars(
        select(QuizAttempt)
        .options(
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.question)
            .selectinload(Question.answer_choices),
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.selected_choice),
        )
        .where(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == current_user.id,
        )
        .order_by(QuizAttempt.submitted_at.desc())
    ).all()

    history: list[QuizAttemptHistoryItem] = []

    for attempt in attempts:
        score = 0
        gradable_questions = 0

        for answer in attempt.answers:
            is_correct = grade_attempt_answer(
                answer.question,
                answer,
            )

            if is_correct is not None:
                gradable_questions += 1

                if is_correct:
                    score += 1

        history.append(
            QuizAttemptHistoryItem(
                attempt_id=attempt.id,
                submitted_at=attempt.submitted_at,
                score=score,
                gradable_questions=gradable_questions,
                total_questions=len(attempt.answers),
            )
        )

    return history


@router.get(
    "/{quiz_id}/attempts/{attempt_id}/results",
    response_model=QuizAttemptResultResponse,
)
def get_quiz_attempt_results(
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizAttemptResultResponse:
    attempt = db.scalar(
        select(QuizAttempt)
        .options(
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.question)
            .selectinload(Question.answer_choices),
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.selected_choice),
        )
        .where(
            QuizAttempt.id == attempt_id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == current_user.id,
        )
    )

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found",
        )

    result_answers: list[QuizAttemptResultAnswer] = []
    score = 0
    gradable_questions = 0

    for answer in attempt.answers:
        question = answer.question
        is_correct = grade_attempt_answer(question, answer)

        if is_correct is not None:
            gradable_questions += 1

            if is_correct:
                score += 1

        answer_choices: list[QuizAttemptResultChoice] = []

        if question.question_type == "multiple_choice":
            submitted_answer = (
                answer.selected_choice.text
                if answer.selected_choice
                else ""
            )

            correct_choice = next(
                (
                    choice
                    for choice in question.answer_choices
                    if choice.is_correct
                ),
                None,
            )

            correct_answer = (
                correct_choice.text
                if correct_choice
                else None
            )

            answer_choices = [
                QuizAttemptResultChoice(
                    id=choice.id,
                    text=choice.text,
                    is_correct=choice.is_correct,
                    was_selected=(
                        choice.id == answer.selected_choice_id
                    ),
                    position=choice.position,
                )
                for choice in sorted(
                    question.answer_choices,
                    key=lambda choice: choice.position,
                )
            ]

        elif question.question_type == "math_work":
            submitted_answer = answer.text_answer or ""
            correct_answer = question.expected_answer

        else:
            submitted_answer = answer.text_answer or ""
            correct_answer = None

        result_answers.append(
            QuizAttemptResultAnswer(
                answer_choices=answer_choices,
                question_id=question.id,
                question_text=question.text,
                question_type=question.question_type,
                is_correct=is_correct,
                submitted_answer=submitted_answer,
                correct_answer=correct_answer,
            )
        )

    return QuizAttemptResultResponse(
        attempt_id=attempt.id,
        quiz_id=attempt.quiz_id,
        score=score,
        gradable_questions=gradable_questions,
        total_questions=len(attempt.answers),
        answers=result_answers,
    )


@router.get(
    "/{quiz_id}/attempts/{attempt_id}/results/pdf",
    response_class=Response,
)
def export_quiz_attempt_results_pdf(
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    results = get_quiz_attempt_results(
        quiz_id=quiz_id,
        attempt_id=attempt_id,
        db=db,
        current_user=current_user,
    )

    quiz = db.scalar(
        select(Quiz).where(Quiz.id == quiz_id)
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    pdf_bytes = build_quiz_result_pdf(
        quiz_title=quiz.title,
        score=results.score,
        gradable_questions=results.gradable_questions,
        total_questions=results.total_questions,
        answers=results.answers,
    )

    safe_title = "".join(
        character
        if character.isalnum() or character in {"-", "_"}
        else "-"
        for character in quiz.title
    ).strip("-")

    filename = (
        f"{safe_title or 'quiz'}-results.pdf"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
        },
    )