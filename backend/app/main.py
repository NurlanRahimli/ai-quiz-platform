from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.quizzes import router as quizzes_router

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}