# Talk to GrailBot (MCP server)

GrailBot ships an [MCP](https://modelcontextprotocol.io) server so you can use the
engine from any MCP client — Claude Desktop, Cursor, etc. — in natural language.
It runs in mock mode with **no keys**, so you can try it in a minute.

## Install & run
```bash
pip install -e ".[mcp]"
python -m grailbot.mcp_server        # stdio transport
```

## Tools
| Tool | What you can ask |
|---|---|
| `grailbot_resolve_card` | "Resolve `2024 Donruss Optic Jaden Daniels Blue Glitter #248`" |
| `grailbot_value_card` | "Is this card a deal at $95?" |
| `grailbot_scan_opportunities` | "Show me the recommended cards right now" |
| `grailbot_paper_trade` | "Paper-trade the recommendations on a $25k bankroll" |

All tools are read-only. In mock mode they run on bundled sample data; set
`GRAILBOT_MODE=live` (with keys in `.env`) to run against real listings.

## Claude Desktop config
Add to `claude_desktop_config.json` (Settings → Developer → Edit Config):
```json
{
  "mcpServers": {
    "grailbot": {
      "command": "python",
      "args": ["-m", "grailbot.mcp_server"],
      "cwd": "/absolute/path/to/card-market-papertrader",
      "env": { "GRAILBOT_MODE": "mock" }
    }
  }
}
```
Restart Claude Desktop; you'll see the four `grailbot_*` tools. Try:
> "Use GrailBot to resolve and value `2024 Donruss Optic Jaden Daniels Blue Glitter #248` at $95."
