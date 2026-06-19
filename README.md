# geo-agent

An MCP server that gives AI agents access to live earth-science data — earthquakes, climate, and weather — through the [Model Context Protocol](https://modelcontextprotocol.io).

## Why

Most AI agents can talk *about* the world but can't see what's happening in it right now. This server exposes real, current geophysical data as tools any MCP-compatible client (Claude Desktop, Cursor, etc.) can call directly.

## Tools

- `get_recent_earthquakes(min_magnitude, days)` — recent significant earthquakes worldwide, via USGS

More tools (climate point data, historical weather) coming as this project grows. See commit history for progress.

## Running it

```bash
uv sync
uv run mcp dev server.py
```
This opens the MCP Inspector for testing tools directly in the browser.

## Status

Early and actively being built in public. Part of a larger project to build an agent that reasons across live data, research literature, and forecasting models.
