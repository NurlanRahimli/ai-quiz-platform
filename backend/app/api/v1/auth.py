from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    generate_otp,
    hash_otp,
    hash_password,
    verify_password,
    verify_otp,
)
from app.models.email_verification import EmailVerification
from app.models.password_reset import PasswordReset
from app.models.user import User
from app.schemas.user import (
    AccountDeleteRequest,
    RegistrationPendingResponse,
    PasswordChangeRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
    EmailVerificationRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    PasswordResetVerificationRequest,
    PasswordResetVerificationResponse,
    PasswordResetRequest,
    PasswordResetResponse,
)
from app.services.email_service import (
    EmailDeliveryError,
    send_password_reset_email,
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
    if user_data.display_name is not None:
        display_name_owner = db.scalar(
            select(User).where(
                func.lower(User.display_name)
                == user_data.display_name.lower(),
                User.id != current_user.id,
            )
        )

        if display_name_owner is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Display name is already taken",
            )

        current_user.display_name = user_data.display_name

    db.add(current_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Display name is already taken",
        )

    db.refresh(current_user)

    return current_user

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_me(
    delete_data: AccountDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if not verify_password(
        delete_data.password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect",
        )

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == current_user.email
        )
    )

    if verification is not None:
        db.delete(verification)

    db.delete(current_user)
    db.commit()


@router.patch(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
)
def change_password(
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if not verify_password(
        password_data.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if verify_password(
        password_data.new_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    current_user.password_hash = hash_password(
        password_data.new_password
    )

    db.add(current_user)
    db.commit()


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

    display_name_owner = db.scalar(
        select(User).where(
            func.lower(User.display_name)
            == user_data.display_name.lower()
        )
    )

    if display_name_owner is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Display name is already taken",
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

    display_name_owner = db.scalar(
        select(User).where(
            func.lower(User.display_name)
            == verification.display_name.lower()
        )
    )

    if display_name_owner is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Display name is already taken",
        )

    user = User(
        email=verification.email,
        display_name=verification.display_name,
        password_hash=verification.password_hash,
    )

    db.add(user)
    db.delete(verification)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Display name is already taken",
        )

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
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def forgot_password(
    request_data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    generic_response = ForgotPasswordResponse(
        message=(
            "If an account exists for this email, "
            "a password reset code has been sent."
        )
    )

    user = db.scalar(
        select(User).where(User.email == request_data.email)
    )

    # Do not reveal whether an account exists for this email.
    if user is None:
        return generic_response

    existing_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == request_data.email
        )
    )

    now = datetime.now(timezone.utc)

    if existing_reset is not None:
        last_sent_at = existing_reset.last_sent_at

        if last_sent_at.tzinfo is None:
            last_sent_at = last_sent_at.replace(
                tzinfo=timezone.utc
            )

        seconds_since_last_send = (
            now - last_sent_at
        ).total_seconds()

        if (
            seconds_since_last_send
            < settings.email_otp_resend_cooldown_seconds
        ):
            # Return the same response rather than exposing
            # password-reset state for an account.
            return generic_response

    otp = generate_otp()
    otp_hash = hash_otp(otp)
    expires_at = now + timedelta(
        minutes=settings.email_otp_expire_minutes
    )

    try:
        send_password_reset_email(
            to_email=user.email,
            otp=otp,
        )
    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send password reset email",
        ) from exc

    if existing_reset is not None:
        existing_reset.otp_hash = otp_hash
        existing_reset.expires_at = expires_at
        existing_reset.attempt_count = 0
        existing_reset.last_sent_at = now
    else:
        password_reset = PasswordReset(
            email=user.email,
            otp_hash=otp_hash,
            expires_at=expires_at,
            attempt_count=0,
            last_sent_at=now,
        )
        db.add(password_reset)

    db.commit()

    return generic_response


@router.post(
    "/verify-password-reset",
    response_model=PasswordResetVerificationResponse,
)
def verify_password_reset(
    verification_data: PasswordResetVerificationRequest,
    db: Session = Depends(get_db),
) -> PasswordResetVerificationResponse:
    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == verification_data.email
        )
    )

    if password_reset is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset code",
        )

    now = datetime.now(timezone.utc)

    expires_at = password_reset.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    if expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset code",
        )

    if (
        password_reset.attempt_count
        >= settings.email_otp_max_attempts
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification attempts",
        )

    if not verify_otp(
        verification_data.otp,
        password_reset.otp_hash,
    ):
        password_reset.attempt_count += 1
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    user = db.scalar(
        select(User).where(
            User.email == password_reset.email
        )
    )

    if user is None:
        db.delete(password_reset)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset code",
        )

    reset_token = create_password_reset_token(
        password_reset.email
    )

    return PasswordResetVerificationResponse(
        reset_token=reset_token,
    )


@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
)
def reset_password(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    email = decode_password_reset_token(
        reset_data.reset_token
    )

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == email
        )
    )

    if password_reset is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    now = datetime.now(timezone.utc)

    expires_at = password_reset.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    if expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if user is None:
        db.delete(password_reset)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    user.password_hash = hash_password(
        reset_data.new_password
    )

    db.delete(password_reset)
    db.commit()

    return PasswordResetResponse(
        message="Password reset successfully"
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