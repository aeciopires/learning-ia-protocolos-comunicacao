"""Fluxo Authorization Code com PKCE, feito pelo host. A senha só é entregue ao provedor de identidade."""

import base64
import hashlib
import html
import re
import secrets
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import httpx

REDIRECT_URI = "http://localhost/callback"


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str
    expires_in: int


def pkce_pair() -> tuple[str, str]:
    """O challenge vai na autorização, e o verifier só na troca: interceptar o código não basta."""
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


class OAuthClient:
    def __init__(self, issuer: str, client_id: str) -> None:
        self._base = f"{issuer}/protocol/openid-connect"
        self._client_id = client_id

    async def login(self, username: str, password: str, scope: str) -> Tokens:
        verifier, challenge = pkce_pair()
        state = secrets.token_urlsafe(16)
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as http:
            page = await http.get(
                f"{self._base}/auth",
                params={
                    "client_id": self._client_id,
                    "response_type": "code",
                    "redirect_uri": REDIRECT_URI,
                    "scope": scope,
                    "state": state,
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                },
            )
            page.raise_for_status()
            # Um navegador faria este passo; aqui o script simula a pessoa preenchendo o login.
            form = re.search(r'action="([^"]+)"', page.text)
            if form is None:
                raise RuntimeError("Login form not found")
            answer = await http.post(html.unescape(form.group(1)), data={"username": username, "password": password})
            if answer.status_code != 302:
                raise RuntimeError(f"Login failed with status {answer.status_code}")
            query = parse_qs(urlparse(answer.headers["location"]).query)
            if query["state"][0] != state:
                raise RuntimeError("State mismatch")
            return await self._token(
                http,
                {
                    "grant_type": "authorization_code",
                    "code": query["code"][0],
                    "redirect_uri": REDIRECT_URI,
                    "code_verifier": verifier,
                },
            )

    async def refresh(self, refresh_token: str) -> Tokens:
        async with httpx.AsyncClient(timeout=20) as http:
            return await self._token(http, {"grant_type": "refresh_token", "refresh_token": refresh_token})

    async def _token(self, http: httpx.AsyncClient, data: dict[str, str]) -> Tokens:
        response = await http.post(f"{self._base}/token", data={**data, "client_id": self._client_id})
        response.raise_for_status()
        body = response.json()
        return Tokens(body["access_token"], body["refresh_token"], body["expires_in"])
