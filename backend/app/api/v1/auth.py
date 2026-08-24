from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    generate_otp,
    hash_otp,
    hash_password,
    verify_password,
    verify_otp,
)
from app.models.email_verification import EmailVerification
from app.models.user import User
from app.schemas.user import (
    RegistrationPendingResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
    EmailVerificationRequest,
    ResendVerificationRequest,
)
from app.services.email_service import (
    EmailDeliveryError,
    send_verification_email,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
)
def update_me(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    current_user.display_name = user_data.display_name

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user
    

@router.post(
    "/register",
    response_model=RegistrationPendingResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
) -> RegistrationPendingResponse:
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    existing_verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == user_data.email
        )
    )

    now = datetime.now(timezone.utc)
    otp = generate_otp()

    password_hash = hash_password(user_data.password)
    otp_hash = hash_otp(otp)
    expires_at = now + timedelta(
        minutes=settings.email_otp_expire_minutes
    )

    try:
        send_verification_email(
            to_email=user_data.email,
            otp=otp,
        )
    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send verification email",
        ) from exc

    if existing_verification:
        existing_verification.display_name = user_data.display_name
        existing_verification.password_hash = password_hash
        existing_verification.otp_hash = otp_hash
        existing_verification.expires_at = expires_at
        existing_verification.attempt_count = 0
        existing_verification.last_sent_at = now
    else:
        verification = EmailVerification(
            email=user_data.email,
            display_name=user_data.display_name,
            password_hash=password_hash,
            otp_hash=otp_hash,
            expires_at=expires_at,
            attempt_count=0,
            last_sent_at=now,
        )
        db.add(verification)

    db.commit()

    return RegistrationPendingResponse(
        email=user_data.email,
        message="Verification code sent",
    )


@router.post(
    "/verify-email",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db),
) -> User:
    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == verification_data.email
        )
    )

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending verification found for this email",
        )

    now = datetime.now(timezone.utc)

    expires_at = verification.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired",
        )

    if verification.attempt_count >= settings.email_otp_max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification attempts",
        )

    if not verify_otp(
        verification_data.otp,
        verification.otp_hash,
    ):
        verification.attempt_count += 1
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    existing_user = db.scalar(
        select(User).where(User.email == verification.email)
    )

    if existing_user:
        db.delete(verification)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=verification.email,
        display_name=verification.display_name,
        password_hash=verification.password_hash,
    )

    db.add(user)
    db.delete(verification)
    db.commit()
    db.refresh(user)

    return user



@router.post(
    "/resend-verification",
    response_model=RegistrationPendingResponse,
)
def resend_verification(
    resend_data: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> RegistrationPendingResponse:
    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == resend_data.email
        )
    )

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending verification found for this email",
        )

    now = datetime.now(timezone.utc)

    last_sent_at = verification.last_sent_at
    if last_sent_at.tzinfo is None:
        last_sent_at = last_sent_at.replace(tzinfo=timezone.utc)

    seconds_since_last_send = (
        now - last_sent_at
    ).total_seconds()

    if (
        seconds_since_last_send
        < settings.email_otp_resend_cooldown_seconds
    ):
        retry_after = (
            settings.email_otp_resend_cooldown_seconds
            - int(seconds_since_last_send)
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Please wait {retry_after} seconds "
                "before requesting another code"
            ),
        )

    otp = generate_otp()

    try:
        send_verification_email(
            to_email=verification.email,
            otp=otp,
        )
    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send verification email",
        ) from exc

    verification.otp_hash = hash_otp(otp)
    verification.expires_at = now + timedelta(
        minutes=settings.email_otp_expire_minutes
    )
    verification.attempt_count = 0
    verification.last_sent_at = now

    db.commit()

    return RegistrationPendingResponse(
        email=verification.email,
        message="Verification code resent",
    )



@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.scalar(
        select(User).where(User.email == credentials.email)
    )

    if user is None or not verify_password(
        credentials.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = create_access_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
    )