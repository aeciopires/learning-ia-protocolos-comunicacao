"""Resource server: nunca vê senha, só valida tokens e aplica o scope de cada tool."""

import logging
import os

import jwt
from labs_common.mcp_http import serve
from labs_common.telemetry import OperationMetrics, setup_telemetry
from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import AnyHttpUrl

from lab_11_oauth.verifier import JwtVerifier, record_decision

logger = logging.getLogger(__name__)
ISSUER = os.environ.get("OAUTH_ISSUER", "http://keycloak:8080/realms/lab")
RESOURCE = os.environ.get("MCP_RESOURCE", "http://server:8000/mcp")


def require_scope(scope: str) -> None:
    token = get_access_token()
    if token is None or scope not in token.scopes:
        record_decision("refused", f"missing_scope:{scope}")
        logger.warning("call refused: missing scope %s", scope)
        raise ToolError(f"This token does not grant {scope}")
    record_decision("accepted", f"scope:{scope}")


def build_server(verifier: TokenVerifier) -> MCPServer:
    mcp = MCPServer(
        "statements",
        version="1.0.0",
        token_verifier=verifier,
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(ISSUER),
            resource_server_url=AnyHttpUrl(RESOURCE),
            # O Keycloak usa `aud`, conferido no verificador, em vez do parâmetro resource.
            validate_token_resource=False,
        ),
    )
    observed = OperationMetrics()

    @mcp.tool()
    def read_statement() -> dict[str, object]:
        """Read the statement of the authenticated user. Requires orders:read."""
        with observed.observe("read_statement"):
            require_scope("orders:read")
            token = get_access_token()
            return {"subject": token.subject if token else None, "balance": 120.5}

    @mcp.tool()
    def create_card(limit: float) -> dict[str, object]:
        """Create a virtual card. Requires orders:write."""
        with observed.observe("create_card"):
            require_scope("orders:write")
            return {"card": "created", "limit": limit}

    return mcp


def main() -> None:
    setup_telemetry("lab-11-server")
    jwks = jwt.PyJWKClient(f"{ISSUER}/protocol/openid-connect/certs")

    def resolve_key(token: str) -> object:
        return jwks.get_signing_key_from_jwt(token).key

    serve(build_server(JwtVerifier(ISSUER, RESOURCE, resolve_key)), hostnames=["server"])


if __name__ == "__main__":
    main()
