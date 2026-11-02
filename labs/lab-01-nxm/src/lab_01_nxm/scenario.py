"""Cenário: compara os formatos de cada provedor e a curva de crescimento das integrações."""

import json

from lab_01_nxm.formats import (
    GET_ORDER_STATUS,
    RUNTIME_FIELDS,
    adapters_without_standard,
    connections_with_standard,
    to_anthropic,
    to_gemini,
    to_mcp,
    to_openai,
)


def main() -> None:
    for name, converter in (("Anthropic", to_anthropic), ("OpenAI", to_openai), ("Gemini", to_gemini), ("MCP", to_mcp)):
        print(f"\n== Tool definition: {name}")
        print(json.dumps(converter(GET_ORDER_STATUS), indent=2))

    print("\n== How each one requests a tool execution")
    for name, description in RUNTIME_FIELDS.items():
        print(f"{name:10} {description}")

    print("\n== Integration growth (models x tools)")
    print(f"{'models':>7} {'tools':>6} {'no standard':>12} {'protocol':>9}")
    for models, tools in ((3, 4), (10, 20), (20, 100)):
        without = adapters_without_standard(models, tools)
        with_standard = connections_with_standard(models, tools)
        print(f"{models:>7} {tools:>6} {without:>12} {with_standard:>9}")


if __name__ == "__main__":
    main()
