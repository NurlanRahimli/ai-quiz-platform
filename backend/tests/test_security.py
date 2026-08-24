from app.core.security import generate_otp, hash_otp, verify_otp


def test_generate_otp_is_six_digits():
    otp = generate_otp()

    assert len(otp) == 6
    assert otp.isdigit()


def test_hash_otp_does_not_store_plaintext():
    otp = "123456"

    hashed = hash_otp(otp)

    assert hashed != otp
    assert len(hashed) == 64


def test_hash_otp_is_consistent():
    otp = "123456"

    assert hash_otp(otp) == hash_otp(otp)


def test_verify_otp_accepts_correct_code():
    otp = "583921"
    hashed = hash_otp(otp)

    assert verify_otp(otp, hashed) is True


def test_verify_otp_rejects_incorrect_code():
    hashed = hash_otp("583921")

    assert verify_otp("583922", hashed) is False


def test_otp_preserves_leading_zeros():
    otp = "000042"
    hashed = hash_otp(otp)

    assert verify_otp("000042", hashed) is True
    assert verify_otp("42", hashed) is False