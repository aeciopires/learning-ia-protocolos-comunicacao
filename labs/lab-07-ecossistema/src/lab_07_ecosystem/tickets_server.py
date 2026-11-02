"""Server tools-heavy: o valor está em operações delimitadas, no estilo do GitHub MCP."""

from labs_common.mcp_http import serve
from labs_common.telemetry import OperationMetrics, setup_telemetry
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


def build_server() -> MCPServer:
    mcp = MCPServer("tickets", version="1.0.0")
    observed = OperationMetrics()
    tickets: dict[int, dict[str, object]] = {
        1: {"id": 1, "title": "Payment failed on order 2", "state": "open", "labels": ["payment"], "comments": []},
        2: {"id": 2, "title": "Slow search page", "state": "open", "labels": ["performance"], "comments": []},
    }

    def existing(ticket_id: int) -> dict[str, object]:
        if ticket_id not in tickets:
            raise ToolError(f"Ticket {ticket_id} does not exist")
        return tickets[ticket_id]

    @mcp.tool()
    def list_tickets(label: str | None = None) -> list[dict[str, object]]:
        """List open tickets, optionally by label."""
        with observed.observe("list_tickets", server="tickets"):
            return [t for t in tickets.values() if label is None or label in t["labels"]]  # type: ignore[operator]

    @mcp.tool()
    def get_ticket(ticket_id: int) -> dict[str, object]:
        """Read one ticket."""
        with observed.observe("get_ticket", server="tickets"):
            return existing(ticket_id)

    @mcp.tool()
    def open_ticket(title: str, label: str) -> dict[str, object]:
        """Open a new ticket."""
        with observed.observe("open_ticket", server="tickets"):
            new_id = max(tickets) + 1
            tickets[new_id] = {"id": new_id, "title": title, "state": "open", "labels": [label], "comments": []}
            return tickets[new_id]

    @mcp.tool()
    def comment_ticket(ticket_id: int, text: str) -> dict[str, object]:
        """Add a comment to a ticket."""
        with observed.observe("comment_ticket", server="tickets"):
            ticket = existing(ticket_id)
            ticket["comments"].append(text)  # type: ignore[attr-defined]
            return ticket

    @mcp.tool()
    def close_ticket(ticket_id: int) -> dict[str, object]:
        """Close a ticket."""
        with observed.observe("close_ticket", server="tickets"):
            ticket = existing(ticket_id)
            ticket["state"] = "closed"
            return ticket

    @mcp.tool()
    def search_tickets(text: str) -> list[dict[str, object]]:
        """Search tickets by title."""
        with observed.observe("search_tickets", server="tickets"):
            return [t for t in tickets.values() if text.lower() in str(t["title"]).lower()]

    return mcp


def main() -> None:
    setup_telemetry("lab-07-tickets")
    serve(build_server(), hostnames=["tickets"])


if __name__ == "__main__":
    main()
