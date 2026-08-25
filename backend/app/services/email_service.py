import httpx

from app.core.config import settings


class EmailDeliveryError(Exception):
    pass


def build_verification_email(
    *,
    to_email: str,
    otp: str,
) -> dict:
    html_content = f"""
    <!DOCTYPE html>
    <html>
      <body style="
        margin: 0;
        padding: 0;
        background-color: #f5f3ff;
        font-family: Arial, Helvetica, sans-serif;
        color: #111827;
      ">
        <table
          role="presentation"
          width="100%"
          cellspacing="0"
          cellpadding="0"
          style="padding: 40px 16px;"
        >
          <tr>
            <td align="center">
              <table
                role="presentation"
                width="100%"
                cellspacing="0"
                cellpadding="0"
                style="
                  max-width: 520px;
                  background-color: #ffffff;
                  border-radius: 16px;
                  padding: 40px;
                  border: 1px solid #e5e7eb;
                "
              >
                <tr>
                  <td>
                    <div style="
                      font-size: 22px;
                      font-weight: 700;
                      margin-bottom: 28px;
                    ">
                      Quiz<span style="color: #7c3aed;">App</span>
                    </div>

                    <h1 style="
                      margin: 0 0 12px;
                      font-size: 26px;
                      line-height: 1.25;
                    ">
                      Verify your email
                    </h1>

                    <p style="
                      margin: 0 0 28px;
                      color: #6b7280;
                      font-size: 15px;
                      line-height: 1.6;
                    ">
                      Enter the verification code below to finish
                      creating your QuizApp account.
                    </p>

                    <div style="
                      background-color: #f5f3ff;
                      border: 1px solid #ddd6fe;
                      border-radius: 12px;
                      padding: 20px;
                      text-align: center;
                      margin-bottom: 24px;
                    ">
                      <div style="
                        color: #6b7280;
                        font-size: 12px;
                        font-weight: 700;
                        letter-spacing: 1px;
                        margin-bottom: 8px;
                      ">
                        VERIFICATION CODE
                      </div>

                      <div style="
                        color: #6d28d9;
                        font-size: 34px;
                        font-weight: 700;
                        letter-spacing: 8px;
                      ">
                        {otp}
                      </div>
                    </div>

                    <p style="
                      margin: 0 0 12px;
                      color: #374151;
                      font-size: 14px;
                      line-height: 1.6;
                    ">
                      This code expires in
                      {settings.email_otp_expire_minutes} minutes.
                    </p>

                    <p style="
                      margin: 0;
                      color: #9ca3af;
                      font-size: 13px;
                      line-height: 1.6;
                    ">
                      If you didn't create a QuizApp account, you can
                      safely ignore this email.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    return {
        "from": {
            "address": settings.twilio_from_email,
            "name": settings.twilio_from_name,
        },
        "to": [
            {
                "address": to_email,
            }
        ],
        "content": {
            "subject": "Your QuizApp verification code",
            "html": html_content,
        },
    }


def send_verification_email(
    *,
    to_email: str,
    otp: str,
) -> None:
    if (
        not settings.twilio_api_key_sid
        or not settings.twilio_api_key_secret
    ):
        raise EmailDeliveryError(
            "Twilio Email API credentials are not configured"
        )

    message = build_verification_email(
        to_email=to_email,
        otp=otp,
    )

    try:
        response = httpx.post(
            "https://comms.twilio.com/v1/Emails",
            json=message,
            auth=(
                settings.twilio_api_key_sid,
                settings.twilio_api_key_secret,
            ),
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        raise EmailDeliveryError(
            "Failed to send verification email"
        ) from exc

    if not 200 <= response.status_code < 300:
        raise EmailDeliveryError(
            "Twilio Email rejected the verification email"
        )

def build_password_reset_email(
    *,
    to_email: str,
    otp: str,
) -> dict:
    html_content = f"""
    <!DOCTYPE html>
    <html>
      <body style="
        margin: 0;
        padding: 0;
        background-color: #050b18;
        font-family: Arial, Helvetica, sans-serif;
        color: #f8fafc;
      ">
        <table
          role="presentation"
          width="100%"
          cellspacing="0"
          cellpadding="0"
          style="
            width: 100%;
            background-color: #050b18;
            padding: 48px 16px;
          "
        >
          <tr>
            <td align="center">
              <table
                role="presentation"
                width="100%"
                cellspacing="0"
                cellpadding="0"
                style="
                  max-width: 520px;
                  background-color: #0b1426;
                  border-radius: 16px;
                  padding: 40px;
                  border: 1px solid #202d47;
                "
              >
                <tr>
                  <td>
                    <div style="
                      font-size: 22px;
                      font-weight: 700;
                      margin-bottom: 28px;
                      color: #f8fafc;
                    ">
                      Quiz<span style="color: #9b6cf5;">App</span>
                    </div>

                    <h1 style="
                      margin: 0 0 12px;
                      color: #f8fafc;
                      font-size: 26px;
                      line-height: 1.25;
                    ">
                      Reset your password
                    </h1>

                    <p style="
                      margin: 0 0 28px;
                      color: #a7b0c0;
                      font-size: 15px;
                      line-height: 1.6;
                    ">
                      We received a request to reset your QuizApp
                      password. Enter the code below to continue.
                    </p>

                    <div style="
                      background-color: #111a33;
                      border: 1px solid #4c347d;
                      border-radius: 12px;
                      padding: 22px;
                      text-align: center;
                      margin-bottom: 24px;
                    ">
                      <div style="
                        color: #9ca6b8;
                        font-size: 12px;
                        font-weight: 700;
                        letter-spacing: 1px;
                        margin-bottom: 10px;
                      ">
                        PASSWORD RESET CODE
                      </div>

                      <div style="
                        color: #a875ff;
                        font-size: 34px;
                        font-weight: 700;
                        letter-spacing: 8px;
                      ">
                        {otp}
                      </div>
                    </div>

                    <p style="
                      margin: 0 0 12px;
                      color: #d7dce5;
                      font-size: 14px;
                      line-height: 1.6;
                    ">
                      This code expires in
                      {settings.email_otp_expire_minutes} minutes.
                    </p>

                    <p style="
                      margin: 0;
                      color: #778195;
                      font-size: 13px;
                      line-height: 1.6;
                    ">
                      If you didn't request a password reset, you can
                      safely ignore this email. Your password will
                      remain unchanged.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    return {
        "from": {
            "address": settings.twilio_from_email,
            "name": settings.twilio_from_name,
        },
        "to": [
            {
                "address": to_email,
            }
        ],
        "content": {
            "subject": "Reset your QuizApp password",
            "html": html_content,
        },
    }

def send_password_reset_email(
    *,
    to_email: str,
    otp: str,
) -> None:
    if (
        not settings.twilio_api_key_sid
        or not settings.twilio_api_key_secret
    ):
        raise EmailDeliveryError(
            "Twilio Email API credentials are not configured"
        )

    message = build_password_reset_email(
        to_email=to_email,
        otp=otp,
    )

    try:
        response = httpx.post(
            "https://comms.twilio.com/v1/Emails",
            json=message,
            auth=(
                settings.twilio_api_key_sid,
                settings.twilio_api_key_secret,
            ),
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        raise EmailDeliveryError(
            "Failed to send password reset email"
        ) from exc

    if not 200 <= response.status_code < 300:
        raise EmailDeliveryError(
            "Twilio Email rejected the password reset email"
        )
