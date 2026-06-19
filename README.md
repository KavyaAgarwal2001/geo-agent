# geo-agent

Live earth-science data, in two shapes: a tool for AI agents, and an app for humans.

- 🔗 **Live demo:** https://kavyaagarwal-geo-agent.streamlit.app
- 🔧 **MCP server:** exposes the same data as tools for any [MCP](https://modelcontextprotocol.io) compatible AI client (Claude Desktop, Cursor, etc.)
- 📝 **Writeup:** https://kavya855084.substack.com/p/building-geo-agent-an-mcp-server

## What this is

This project exposes earth-science data through multiple interfaces, because they solve different problems.

- **The Streamlit app** is for humans. Open it, click around, look at charts and maps.
- **The MCP server** is for agents. It lets an AI assistant decide, on its own, to pull live data or search reference material as one step while reasoning about something else entirely.

Started with live earthquake and climate data (USGS, NASA POWER), connected to Claude Desktop to confirm agentic tool use, and is now adding retrieval over real climate science literature.

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
Two tabs, same underlying data sources, built for human exploration: an interactive earthquake map and a climate time-series explorer, both with live filtering.

```bash
uv run streamlit run app.py
```

### 3. Climate paper search (in progress)
A local retrieval-augmented search system over real climate science reports (IPCC AR6, SR15), so questions can be answered with grounded, cited passages instead of relying on a model's training data alone.

- `ingest.py`: extracts text from PDFs in `papers/`, splits it into overlapping chunks, embeds them with `sentence-transformers` (`all-MiniLM-L6-v2`), and stores them in a local [Chroma](https://www.trychroma.com) vector database.
- `tests/test_retrieval.py`: a pytest suite validating retrieval quality across multiple real climate questions, not just a single spot-checked query.

```bash
uv run python ingest.py
uv run pytest tests/test_retrieval.py -v
```

An MCP tool wrapping this search (`search_climate_papers`) is the next step, not yet wired into `server.py`.

## Tech stack
Python, MCP SDK, Streamlit, Plotly, httpx, Chroma, sentence-transformers, pytest, uv

## Status
See commit history for progress. Currently building: an MCP tool exposing climate-paper search, then a router agent that decides which of the available tools (live data vs. paper search) to use for a given question.

## Author
Kavya Agarwal. [Website](https://kavyaagarwal2001.github.io) · [LinkedIn](https://in.linkedin.com/in/kavya-agarwal-5a77611a4)
