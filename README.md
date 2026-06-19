# geo-agent

Live earth-science data, in two shapes: a tool for AI agents, and an app for humans.

- 🔗 **Live demo:** https://kavyaagarwal-geo-agent.streamlit.app
- 🔧 **MCP server:** exposes the same data as tools for any [MCP](https://modelcontextprotocol.io)-compatible AI client (Claude Desktop, Cursor, etc.)

## What this is

This project exposes earth-science data through two interfaces, because they solve different problems.

- **The Streamlit app** is for humans. Open it, drag sliders, look at a map.
- **The MCP server** is for agents. It lets an AI assistant decide, on its own, to pull live data as one step while reasoning about something else entirely. No dashboard required, no human has to know this tool exists.

Started with earthquakes (USGS), now also covers climate data (NASA POWER). More tools in progress.

## Components

### 1. MCP server (`server.py`)
Exposes earth-science data as tools any MCP client can call.

**Tools:**
- `get_recent_earthquakes(min_magnitude, days)`: recent significant earthquakes worldwide, via [USGS](https://earthquake.usgs.gov). Read-only, annotated.
- `get_climate_point_data(latitude, longitude, days)`: recent daily temperature, precipitation, and solar radiation for any location, via [NASA POWER](https://power.larc.nasa.gov). Read-only, annotated. Handles NASA's processing-lag fill values gracefully instead of printing raw placeholder data.

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

## Tech stack
Python, MCP SDK, Streamlit, Plotly, httpx, uv

## Status
See commit history for progress. Next up: a historical weather tool, then connecting this server to an MCP client (Claude Desktop) so an agent can choose between tools live, on its own.

## Author
Kavya Agarwal. [Website](https://kavyaagarwal2001.github.io) · [LinkedIn](https://in.linkedin.com/in/kavya-agarwal-5a77611a4)
