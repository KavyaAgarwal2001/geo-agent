# geo-agent

Live earth-science data, in two shapes: a tool for AI agents, and an app for humans.

🔗 **Live demo:** https://kavyaagarwal-geo-agent.streamlit.app
🔧 **MCP server:** exposes the same data as tools for any [MCP](https://modelcontextprotocol.io)-compatible AI client (Claude Desktop, Cursor, etc.)

## What this is

Most "AI + data" projects pick one interface. This one deliberately builds two, on the same underlying data logic, because they solve different problems.

- **The Streamlit app** is for humans. Open it, drag sliders, look at a map.
- **The MCP server** is for agents. It lets an AI assistant decide, on its own, to pull live earthquake data as one step while reasoning about something else entirely. No dashboard required, no human has to know this tool exists.

Starting with earthquakes (USGS), growing to cover climate and weather data next.

## Components

### 1. MCP server (`server.py`)
Exposes earth-science data as tools any MCP client can call.

**Tools:**
- `get_recent_earthquakes(min_magnitude, days)`: recent significant earthquakes worldwide, via [USGS](https://earthquake.usgs.gov). Read-only, annotated.

```bash
uv sync
uv run mcp dev server.py
```
Opens the MCP Inspector in your browser for testing tools directly.

### 2. Live web app (`app.py`)
Interactive earthquake explorer, using the same USGS data, built for human exploration: live filtering by magnitude and time window, a magnitude reference guide, and a raw data table.

```bash
uv run streamlit run app.py
```
Or just visit the live deployed version: https://kavyaagarwal-geo-agent.streamlit.app

## Tech stack
Python, MCP SDK, Streamlit, Plotly, httpx, uv

## Status
Early and being built in public. See commit history for progress. Next up: a climate/weather data tool (NASA POWER), then a router agent that reasons across live data, research literature, and forecasting models.

## Author
Kavya Agarwal. [Website](https://kavyaagarwal2001.github.io) · [LinkedIn](https://in.linkedin.com/in/kavya-agarwal-5a77611a4)
