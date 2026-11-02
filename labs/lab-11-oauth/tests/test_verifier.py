import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from lab_11_oauth.oauth_client import pkce_pair
from lab_11_oauth.verifier import JwtVerifier

ISSUER = "http://idp.example/realms/lab"
AUDIENCE = "http://server:8000/mcp"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def token(**overrides: object) -> str:
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "azp": "lab-host",
        "sub": "u1",
        "scope": "orders:read",
        "exp": int(time.time()) + 60,
    }
    claims.update(overrides)
    return jwt.encode(claims, KEY, algorithm="RS256")


@pytest.fixture
def verifier() -> JwtVerifier:
    return JwtVerifier(ISSUER, AUDIENCE, lambda _: KEY.public_key())


async def test_valid_token_exposes_scopes(verifier: JwtVerifier) -> None:
    access = await verifier.verify_token(token())
    assert access is not None
    assert access.scopes == ["orders:read"]


@pytest.mark.parametrize(
    "overrides",
    [{"aud": "http://other"}, {"iss": "http://evil"}, {"exp": int(time.time()) - 60}],
)
async def test_invalid_claims_are_refused(verifier: JwtVerifier, overrides: dict[str, object]) -> None:
    assert await verifier.verify_token(token(**overrides)) is None


async def test_token_signed_by_another_key_is_refused(verifier: JwtVerifier) -> None:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    forged = jwt.encode({"iss": ISSUER, "aud": AUDIENCE, "exp": int(time.time()) + 60}, other, algorithm="RS256")
    assert await verifier.verify_token(forged) is None


def test_pkce_pair_is_unique() -> None:
    assert pkce_pair() != pkce_pair()
