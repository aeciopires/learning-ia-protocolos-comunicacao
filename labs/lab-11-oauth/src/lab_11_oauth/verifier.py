"""Valida o JWT: assinatura, emissor, validade e, sobretudo, se o token foi emitido para este server."""

import asyncio
import logging
from collections.abc import Callable

import jwt
from labs_common.telemetry import meter
from mcp.server.auth.provider import AccessToken, TokenVerifier

logger = logging.getLogger(__name__)
KeyResolver = Callable[[str], object]


def record_decision(decision: str, reason: str) -> None:
    meter().create_counter("lab.authorization.decisions", description="Authorization decisions").add(
        1, {"decision": decision, "reason": reason}
    )


class JwtVerifier(TokenVerifier):
    def __init__(self, issuer: str, audience: str, key_resolver: KeyResolver) -> None:
        self._issuer, self._audience, self._key_resolver = issuer, audience, key_resolver

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            # A busca da chave faz uma chamada de rede bloqueante, por isso roda em uma thread.
            key = await asyncio.to_thread(self._key_resolver, token)
            claims = jwt.decode(token, key, algorithms=["RS256"], audience=self._audience, issuer=self._issuer)  # type: ignore[arg-type]
        except jwt.InvalidAudienceError:
            # Aceitar token emitido para outro serviço é o caminho do confused deputy.
            return self._refuse("wrong_audience")
        except jwt.ExpiredSignatureError:
            return self._refuse("expired")
        except jwt.InvalidTokenError:
            return self._refuse("invalid_token")
        record_decision("accepted", "valid_token")
        # O token nunca vai para log nem é repassado a APIs downstream.
        return AccessToken(
            token=token,
            client_id=claims.get("azp", "unknown"),
            scopes=claims.get("scope", "").split(),
            expires_at=claims.get("exp"),
            subject=claims.get("sub"),
            resource=self._audience,
        )

    @staticmethod
    def _refuse(reason: str) -> None:
        record_decision("refused", reason)
        logger.warning("token refused: %s", reason)
