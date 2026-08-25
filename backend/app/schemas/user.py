import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.quiz import (
    QuizDiscoveryResponse,
    QuizListResponse,
)


class UserRegister(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if len(value) < 2:
            raise ValueError("Display name must contain at least 2 characters")

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class RegistrationPendingResponse(BaseModel):
    email: EmailStr
    message: str


class EmailVerificationRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Verification code must contain only digits")
        return value


class ResendVerificationRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class UserUpdate(BaseModel):
    display_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Display name must contain at least 2 characters"
            )

        return value



class AccountDeleteRequest(BaseModel):
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    display_name: str
    is_active: bool
    created_at: datetime


class PublicUserProfileResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    created_at: datetime
    public_quiz_count: int
    follower_count: int
    following_count: int
    is_following: bool
    quizzes: list[QuizDiscoveryResponse]
    page: int
    page_size: int
    total_pages: int


class UserQuizPageResponse(BaseModel):
    quizzes: list[QuizListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserFollowResponse(BaseModel):
    user_id: uuid.UUID
    is_following: bool


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"