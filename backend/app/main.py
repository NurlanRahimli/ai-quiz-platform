from fastapi import FastAPI

from app.api.v1.auth import router as auth_router


app = FastAPI(
    title="AI Quiz Platform API",
    version="1.0.0",
)

app.include_router(
    auth_router,
    prefix="/api/v1",
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}