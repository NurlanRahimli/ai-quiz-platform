from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.quizzes import router as quizzes_router
from app.api.v1.questions import router as questions_router
from app.api.v1.attempts import (
    router as attempts_router,
    user_attempts_router,
)
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.dashboard import router as dashboard_router

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="AI Quiz Platform API",
    version="1.0.0",
)

app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    quizzes_router,
    prefix="/api/v1",
)

app.include_router(
    audit_logs_router,
    prefix="/api/v1",
)

app.include_router(
    users_router,
    prefix="/api/v1",
)
app.include_router(
    dashboard_router,
    prefix="/api/v1",
)
app.include_router(
    attempts_router,
    prefix="/api/v1",
)

app.include_router(
    user_attempts_router,
    prefix="/api/v1",
)

app.include_router(
    questions_router,
    prefix="/api/v1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}