import pytest
from datetime import timedelta

from app.core.security import AuthError, create_access_token, decode_access_token


def test_expired_token_rejected() -> None:
    token = create_access_token(subject="1", expires_delta=timedelta(seconds=-1))
    with pytest.raises(AuthError):
        decode_access_token(token)
